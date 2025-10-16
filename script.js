// API configuration
const API_BASE_URL = 'http://localhost:8000';

// Search functionality that calls the FastAPI backend
async function performSearch() {
    const searchInput = document.getElementById('searchInput');
    const resultsContainer = document.getElementById('results');
    const query = searchInput.value.trim();
    
    if (!query) {
        alert('Please enter a search query');
        return;
    }
    
    // Show loading state
    resultsContainer.innerHTML = '<div class="loading">Searching...</div>';
    
    try {
        // Call the FastAPI backend
        const response = await fetch(`${API_BASE_URL}/search`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: query,
                top_k: 5
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Display the results
        displayResults(data.results, query, data.ai_response);
        
    } catch (error) {
        console.error('Search error:', error);
        resultsContainer.innerHTML = `
            <div class="error">
                Error performing search: ${error.message}<br>
                Make sure the backend server is running on port 8000.
            </div>
        `;
    }
}

function displayResults(results, query, aiResponse) {
    const resultsContainer = document.getElementById('results');
    
    if (!results || results.length === 0) {
        resultsContainer.innerHTML = '<div class="no-results">No results found for your query.</div>';
        return;
    }
    
    let html = `
        <div class="ai-response-container">
            <h2 style="color: #4a90e2; margin-bottom: 15px; text-align: center;">AI Response</h2>
            <div class="ai-response">
                ${aiResponse || 'AI response not available'}
            </div>
        </div>
        
        <div class="search-results-container">
            <h2 style="color: #ffffff; margin-bottom: 20px; text-align: center; margin-top: 30px;">Source Results for: "${query}"</h2>
    `;
    
    results.forEach((result, index) => {
        html += `
            <div class="result-item">
                <div class="result-score">Similarity Score: ${result.score.toFixed(4)}</div>
                <div class="result-id">Airtable ID: ${result.id}</div>
                <div class="result-text">${result.metadata.searchable_text}</div>
            </div>
        `;
    });
    
    html += '</div>';
    resultsContainer.innerHTML = html;
}

// Allow Enter key to trigger search
document.getElementById('searchInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        performSearch();
    }
});

// Focus on search input when page loads
window.addEventListener('load', function() {
    document.getElementById('searchInput').focus();
});
