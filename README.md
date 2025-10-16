# Cosmos-Hiring-Assessment

This directory offers some example scripts that the tema would use to ingest data from varying sources and upload that to a vector database.

This directory also creates a basic backend and frontend where the user can query against the database. A user query on the frontend will trigger a cosine similarity against the vector db which will return a set of five or fewer results. We then send this information and the original query to an LLM to make the results human readable and answer the original question.

Note that this directory only provides very basic functionality and proof-of-concept style scripts. The airtable script is the only flushed out and tested version. The other scripts are meant to show that we are able to capture the data effectively and easily, so do not expect them to work out of the box.