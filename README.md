# BIM-to-Graph: Semantic Relationship Extraction

## Overview
This repository provides a specialized data pipeline for extracting structured architectural relationships from BIM (Building Information Modeling) data. By leveraging the **Speckle API**, this tool bypasses raw geometry parsing to natively extract object hierarchies and topological connections.

The goal is to provide a clean, semantic "Node and Edge" list for training **Graph Neural Networks (GNNs)**, ensuring that structural logic—such as which walls host which openings—is preserved as ground-truth data.

## Core Features
- **Semantic Data Pruning:** Implements a blacklist-based filtering system to remove non-structural noise (meshes, textures, and materials), reducing dataset complexity while maintaining topological integrity.
- **Scalable Extraction:** Optimized to handle large-scale building models (10,000+ nodes) through Speckle’s decomposed object storage and chunked data transfer.
- **Graph Transformation:** Automatically converts nested BIM trees into **NetworkX Directed Graphs** for easy integration with ML frameworks like PyTorch Geometric.

## Setup & Installation

1. **Clone the Repository:**
  ```bash
  git clone [https://github.com/](https://github.com/)[your-username]/BIM-to-Graph.git
  cd BIM-to-Graph
  ```
2. **Install Dependencies:**
  ```bash
  pip install specklepy networkx matplotlib python-dotenv
  ```
3. **Add speckle token to environment**
  ```bash
  SPECKLE_TOKEN=your_access_token_here
  ```
## Running
  ```bash
  python speckle_extractor.py
  ```
