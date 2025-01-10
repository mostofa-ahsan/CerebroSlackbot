data_ingestion/
├── data/                              # Data storage and processed files
│   ├── downloads/                     # Raw downloaded files (PPT, DOCX, PDFs, etc.)
│   ├── converted_downloads/           # Converted PDFs from raw files
│   ├── pages_as_pdf/                  # Manually downloaded or scraped PDFs
│   ├── cerebro_chroma_db/             # Chroma DB storage directory
│   │   ├── chroma_embeddings/         # Folder to store enriched embeddings (optional)
│   │   ├── index/                     # Chroma DB index files
│   │   └── chroma-collections/        # Chroma DB collection files
│   ├── indexes/                       # Index files for search and retrieval
│   ├── parsed_text_plain/             # Plain text parsed from PDFs or other documents
│   ├── saved_images/                  # Images saved from scraped pages
│   ├── scraped_pages/                 # HTML files of scraped web pages
│   ├── chunked_text_files/            # Chunked text files for ingestion
│   ├── progress_summary.json          # JSON tracking progress of data ingestion
│   ├── mapped_metadata.json           # JSON mapping metadata to chunks or records
│   └── logs/                          # Logs for ingestion and queries
├── model/                             # Local embedding model storage
│   └── all-mpnet-base-v2/             # Folder for the all-mpnet-base-v2 model
├── scripts/                           # Python scripts for ingestion, query, and utilities
│   ├── authenticator.py               # Handles authentication (e.g., login for web scraping)
│   ├── chunking.py                    # Contains logic for text chunking (hierarchical, by paragraph, etc.)
│   ├── convert_to_pdf.py              # Converts various file formats to PDFs
│   ├── embedding.py                   # Handles embedding logic using local models
│   ├── indexer.py                     # Builds and manages indexes for Chroma DB
│   ├── ingest_to_cerebro_collection_3.py  # Script to ingest data into Chroma DB
│   ├── ingest_to_neo4j.py             # Script to ingest data into Neo4j
│   ├── initialize_chroma_db.py        # Initializes and sets up Chroma DB collections
│   ├── main_ingestion.py              # Master script for running all ingestion tasks
│   ├── map_metadata.py                # Maps metadata to chunks or records
│   ├── pdf_parser.py                  # Extracts text from PDF files
│   ├── query_cerebro_collection_3.py  # Queries the Chroma DB collection
│   ├── scraper_brandcentral.py        # Scrapes BrandCentral or other websites
│   ├── visualize_graph.py             # Visualizes the graph or relationships between data
├── requirements.txt                   # Python dependencies
├── README.md                          # Project documentation
├── .venv/                             # Virtual environment (if applicable)
└── .gitignore                         # Git ignore file
