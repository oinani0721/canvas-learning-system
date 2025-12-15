#!/usr/bin/env python3
"""
Demo usage of the Obsidian Macro Graph Builder System
"""

import os
from obsidian_macro_graph_builder import MacroGraphBuilder

def main():
    print("Demo: Obsidian Macro Document Relationship Graph Construction")
    print("=" * 60)
    
    # Configuration
    vault_path = r"C:\Users\ROG\托福\笔记库"
    target_tag = "#我的课堂总结"
    
    print(f"Vault Path: {vault_path}")
    print(f"Target Tag: {target_tag}")
    
    # Check if vault exists
    if not os.path.exists(vault_path):
        print(f"WARNING: Vault path does not exist: {vault_path}")
        print("Please ensure the path is correct or create some test documents.")
        return
    
    # Create the builder
    builder = MacroGraphBuilder(
        vault_path=vault_path,
        target_tag=target_tag
    )
    
    # Run the system
    result = builder.build_macro_graph()
    
    if result['success']:
        print("\nDEMO COMPLETED SUCCESSFULLY!")
        print(f"Documents processed: {result['documents_processed']}")
        print(f"Themes discovered: {result['themes_discovered']}")
        print(f"Files generated: {result['files_generated']}")
        print(f"Output directory: {result['output_directory']}")
        print(f"Overview file: {result['overview_file']}")
        
        print("\nGenerated files:")
        for file_path in result['generated_files']:
            print(f"  - {os.path.basename(file_path)}")
    else:
        print(f"Demo failed: {result['error']}")

if __name__ == "__main__":
    main()