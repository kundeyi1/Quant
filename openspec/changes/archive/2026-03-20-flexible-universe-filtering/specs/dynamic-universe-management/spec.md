## ADDED Requirements

### Requirement: Index Constituent Reading
The system SHALL support reading index constituent files from `D:\DATA\INDEX_COMP\`. It MUST support CSI 500 (`000905_comp.csv`) and CSI 1000 (`000852_comp.csv`).

#### Scenario: Read CSI 500
- **WHEN** user requests constituents for index `000905`
- **THEN** system loads the file `000905_comp.csv` and returns a DataFrame with `code`, `indate`, and `outdate`

### Requirement: Temporal Member Filtering
The system SHALL filter stocks based on the current date. A stock MUST be included only if `indate <= current_date` and (`outdate > current_date` OR `outdate` is null).

#### Scenario: Valid membership filtering
- **WHEN** a stock has `indate` 2020-01-01 and `outdate` 2021-01-01
- **THEN** it MUST be included for date 2020-06-01 but excluded for 2021-06-01

### Requirement: Unified Data Loading with Universe
The system SHALL provide a method `get_universe_data` that takes a `universe` parameter. This method MUST perform automated filtering of the loaded dataset.

#### Scenario: Integrated CSI 500 test
- **WHEN** user calls `get_universe_data` for CSI 500 between 2023-01-01 and 2023-12-31
- **THEN** the returned DataFrame MUST only contain stocks that were members of CSI 500 during that period
