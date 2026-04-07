## ADDED Requirements

### Requirement: Repository Root LICENSE File

The repository root SHALL contain a `LICENSE` file with valid MIT License text. The copyright line SHALL identify the author as `oinani0721` and the year as `2026`. The file SHALL be plain UTF-8 text with no BOM and no trailing whitespace lines.

#### Scenario: LICENSE file exists at repo root
- **WHEN** `os.path.exists("LICENSE")` is checked from the repository root
- **THEN** the result is `True`

#### Scenario: LICENSE contains MIT identifier
- **WHEN** the contents of `LICENSE` are read
- **THEN** the file contains the substring `MIT License` AND `Copyright (c) 2026 oinani0721` AND `Permission is hereby granted, free of charge`

#### Scenario: README link to LICENSE is reachable
- **WHEN** `README.md` contains a link to `LICENSE` (e.g. `[LICENSE](LICENSE)` or `See LICENSE for terms`)
- **THEN** the linked file resolves to the repository root LICENSE file
