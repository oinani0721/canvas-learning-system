#!/usr/bin/env python3
"""
Architecture Document Sharding Script
Splits large architecture documents by ## headings into smaller files
"""

import os
import re
from pathlib import Path
from typing import List, Tuple

def extract_sections(content: str) -> List[Tuple[str, str, int]]:
    """Extract sections from markdown content by ## headings"""
    sections = []
    lines = content.split('\n')

    current_title = "frontmatter"
    current_content = []
    current_start = 0

    for i, line in enumerate(lines):
        if line.startswith('## '):
            # Save previous section
            if current_content:
                sections.append((current_title, '\n'.join(current_content), len('\n'.join(current_content))))

            # Start new section
            current_title = line[3:].strip()
            current_content = [line]
            current_start = i
        else:
            current_content.append(line)

    # Save last section
    if current_content:
        sections.append((current_title, '\n'.join(current_content), len('\n'.join(current_content))))

    return sections

def sanitize_filename(title: str) -> str:
    """Convert section title to valid filename"""
    # Remove emoji and special chars
    clean = re.sub(r'[^\w\s\u4e00-\u9fff-]', '', title)
    # Replace spaces with hyphens
    clean = re.sub(r'\s+', '-', clean.strip())
    # Lowercase
    return clean.lower()[:50]

def shard_document(filepath: str, output_dir: str, max_size_kb: int = 40) -> dict:
    """Shard a document into smaller files"""
    path = Path(filepath)
    content = path.read_text(encoding='utf-8')

    base_name = path.stem
    shard_dir = Path(output_dir) / base_name.lower()
    shard_dir.mkdir(parents=True, exist_ok=True)

    sections = extract_sections(content)

    # Group small sections together
    shards = []
    current_shard = []
    current_size = 0
    max_size = max_size_kb * 1024

    for title, content, size in sections:
        if current_size + size > max_size and current_shard:
            shards.append(current_shard)
            current_shard = []
            current_size = 0

        current_shard.append((title, content))
        current_size += size

    if current_shard:
        shards.append(current_shard)

    # Write shards
    shard_files = []
    for i, shard in enumerate(shards, 1):
        # Use first section title for filename
        first_title = shard[0][0]
        if first_title == "frontmatter":
            filename = f"{i:02d}-overview.md"
        else:
            filename = f"{i:02d}-{sanitize_filename(first_title)}.md"

        shard_content = '\n\n'.join([content for _, content in shard])

        # Add header
        header = f"# {base_name} - Part {i}\n\n"
        header += f"**Source**: `{path.name}`\n"
        header += f"**Sections**: {', '.join([t for t, _ in shard if t != 'frontmatter'])}\n\n"
        header += "---\n\n"

        full_content = header + shard_content

        shard_path = shard_dir / filename
        shard_path.write_text(full_content, encoding='utf-8')
        shard_files.append({
            'filename': filename,
            'size_kb': len(full_content) // 1024,
            'sections': [t for t, _ in shard if t != 'frontmatter']
        })

    # Create index file
    index_content = f"# {base_name} - Index\n\n"
    index_content += f"**Original File**: `{path.name}`\n"
    index_content += f"**Total Shards**: {len(shards)}\n\n"
    index_content += "## Shards\n\n"

    for shard in shard_files:
        index_content += f"### [{shard['filename']}]({shard['filename']})\n"
        index_content += f"- **Size**: {shard['size_kb']}KB\n"
        index_content += f"- **Sections**: {', '.join(shard['sections'])}\n\n"

    index_path = shard_dir / "INDEX.md"
    index_path.write_text(index_content, encoding='utf-8')

    return {
        'original': filepath,
        'shard_dir': str(shard_dir),
        'shard_count': len(shards),
        'shards': shard_files
    }

def main():
    base_dir = Path("C:/Users/ROG/托福/Canvas/docs/architecture")
    output_dir = base_dir / "shards"

    # Files to shard (P0 and P1)
    files_to_shard = [
        "LANGGRAPH-MEMORY-INTEGRATION-DESIGN.md",
        "GRAPHITI-KNOWLEDGE-GRAPH-INTEGRATION-ARCHITECTURE.md",
        "MULTI-AGENT-CONCURRENT-ANALYSIS-SYSTEM-ARCHITECTURE.md"
    ]

    results = []
    for filename in files_to_shard:
        filepath = base_dir / filename
        if filepath.exists():
            print(f"\nSharding: {filename}")
            result = shard_document(str(filepath), str(output_dir))
            results.append(result)
            print(f"  Created {result['shard_count']} shards in {result['shard_dir']}")
            for shard in result['shards']:
                print(f"    - {shard['filename']} ({shard['size_kb']}KB)")
        else:
            print(f"File not found: {filepath}")

    print("\n✅ Sharding complete!")
    return results

if __name__ == "__main__":
    main()
