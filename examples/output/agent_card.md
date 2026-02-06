# Financial Analyst Agent (v1.0.0)

**Role:** Assistant

## 🔌 API Interface

### Inputs
| Field Name | Type | Required? | Description |
| --- | --- | --- | --- |
| `company_ticker` | `string` | Yes | The stock ticker symbol (e.g., AAPL). |
| `report_year` | `integer` | Yes | The fiscal year for the report. |

### Outputs
| Field Name | Type | Required? | Description |
| --- | --- | --- | --- |
| `disclaimer` | `string` | Yes | Legal disclaimer. |
| `recommendation` | `string` | Yes | Investment recommendation (Buy/Sell/Hold). |
| `summary_text` | `string` | Yes | Detailed markdown summary of the analysis. |