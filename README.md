# Project Overview

This project implements a chatbot for users to interact with the policies for Richmond University that are being stored in the Richmond_Policies_Cleaned folder. The chatbot should come equipped with a frontend for the users to access information on specific policies, and should also be able to retain conversation history.

## Project Workflow

The project logic should be implemented in LangChain, and we need to make different tools that our chatbot can call and use. The chatbot will automatically determine what tool needs to be used based on the context of situation at hand. The chatbot will receive queries from the user on specific policies, for example a user could ask "What is the policy on drinking?". The chatbot implements a RAG pipeline with two step retrieval; the first retrieval step would be finding the relevant files/chunks to the user query, the second step would be retrieving the desired information from the specified chunks. Chunks will be stored semantically in ChromaDB. The user should be able to prompt the chatbot and then retrieve the answer to their query from the chatbot. Conversation history should be stored in a Supabase database so the chatbot can reference its history if need be. The frontend will be built in React, and we will use FastAPI to connect all the parts of our application together.

## Tech Stack

- Python
- LangChain
- Chroma DB
- Supabase
- FastAPI
- React
- Hugging Face (potentially)