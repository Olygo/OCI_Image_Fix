# Changelog
[2.0.0]

## Added

- **Single-image targeting option:** Added a new command-line option allowing users to analyze or repair a specific custom image by OCID.
- **CSV report generation:** The script now generates a detailed CSV report listing all analyzed custom images, including missing schema.
- **Automatic CSV upload:** Implemented automatic upload of the generated CSV report to Object Storage. This feature can be disabled via configuration.
- **Dry-run mode:** Introduced a dry-run option to preview which images require correction without applying any changes.

## Improved
- **Additional validation checks:** Added new control mechanisms to improve accuracy and reliability when analyzing image data.
- **Code optimization:** Refactored core logic for better performance and maintainability.
- **Reporting display:** Enhanced the console output for clearer, more readable reporting during script execution.