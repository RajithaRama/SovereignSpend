# Transaction Rules

The Finance Tracker supports automatic transaction processing using a powerful rules engine. Rules can categorize transactions, link transactions between accounts, and more.

## Rule Types

There are **two types of rules** in this system:

### 1. Simple Pattern Rules (Recommended for Most Users)
Simple JSON rules for basic categorization using pattern matching.

### 2. Advanced Database Rules
More powerful rules stored in the database that can link accounts and perform complex operations.

---

## Simple Pattern Rules (Basic Usage)

### File Location
Store your rules in `rules.json` in the project root. This file is git-ignored for privacy.

### Rule Format

```json
[
  {
    "pattern": "REGEX_PATTERN",
    "category": "Category Name",
    "description": "Human-readable description"
  }
]
```

**Fields:**
- `pattern` (required): Regex pattern to match transaction descriptions
- `category` (required): Category to assign when matched
- `description` (optional): Human-readable note for documentation

### Pattern Matching Tips

1. **Case Insensitive**: All patterns match case-insensitively
2. **Use `.*` for wildcards**: Match any characters
3. **Use `|` for alternatives**: `TESCO|DUNNES|LIDL` matches any store
4. **Anchor with `^` and `$`**: Match start/end of string if needed
5. **Escape special characters**: Use `\.` for literal dots

### Quick Start

1. **Copy an example file:**
   ```bash
   cp rules.example.json rules.json
   ```

2. **Edit `rules.json` with your patterns**

3. **Apply rules:**
   - Automatic: Upload bank statements (rules auto-apply)
   - Manual: Click "Run Rules" button to apply to existing transactions

### Example Rules

```json
[
  {
    "pattern": "SPOTIFY.*",
    "category": "Entertainment",
    "description": "Spotify subscription"
  },
  {
    "pattern": "TESCO.*|LIDL.*|ALDI.*",
    "category": "Groceries",
    "description": "Supermarket purchases"
  },
  {
    "pattern": ".*RESTAURANT.*|.*CAFE.*|.*COFFEE.*",
    "category": "Dining",
    "description": "Restaurants and cafes"
  },
  {
    "pattern": "SALARY.*|PAYROLL.*",
    "category": "Income",
    "description": "Salary payments"
  }
]
```

See `rules.example.json` and `rules.income-housing.example.json` for more examples.

---

## Advanced Database Rules

For power users who need to link transactions between accounts or apply conditional logic.

### Rule Structure

Database rules are stored in the `transaction_rules` table with these fields:

#### Core Fields
- `match_pattern` (required): String to match in transaction description
- `match_type` (default: "contains"): How to match
  - `"contains"`: Pattern appears anywhere in description
  - `"exact"`: Exact match (case-insensitive)
- `origin_type` (optional): Filter by transaction type
  - `"income"`: Only match income transactions
  - `"expense"`: Only match expense transactions
  - `null`: Match both

#### Rule Action
- `rule_type` (required): What action to perform
  - `"update_category"`: Change transaction category
  - `"link_account"`: Create linked transaction in another account

#### For `update_category` Rules
- `category`: New category to assign

#### For `link_account` Rules
- `target_account_id`: ID of account to create linked transaction in
- `target_account_name`: Name of target account (resolved to ID on load)
- `target_type`: Type of linked transaction (`"income"` or `"expense"`)

### Advanced Rule JSON Format

When loaded via `config_loader.py`, use this format in `rules.json`:

```json
[
  {
    "match_pattern": "Transfer to Savings",
    "match_type": "contains",
    "origin_type": "expense",
    "rule_type": "link_account",
    "target_account_name": "Savings Account",
    "target_type": "income",
    "category": "Transfer"
  },
  {
    "match_pattern": "NETFLIX",
    "match_type": "contains",
    "rule_type": "update_category",
    "category": "Entertainment"
  }
]
```

### How Advanced Rules Work

1. **Pattern Matching**: Transaction description is matched against `match_pattern` using `match_type`
2. **Type Filtering**: If `origin_type` is set, only transactions of that type are processed
3. **Action Execution**:
   - **update_category**: Updates the transaction's category
   - **link_account**: Creates a mirrored transaction in the target account
4. **Duplicate Prevention**: The system prevents creating duplicate linked transactions

### Example Use Cases

#### Tracking Transfers Between Accounts
```json
{
  "match_pattern": "Transfer to Savings",
  "match_type": "contains",
  "origin_type": "expense",
  "rule_type": "link_account",
  "target_account_name": "Savings Account",
  "target_type": "income",
  "category": "Transfer"
}
```
When you transfer money from checking to savings, this creates:
- Expense in checking account (original transaction)
- Income in savings account (auto-created linked transaction)

#### Categorizing Expenses
```json
{
  "match_pattern": "STARBUCKS",
  "match_type": "contains",
  "rule_type": "update_category",
  "category": "Coffee"
}
```

---

## Rule Application Order

1. **On Upload**: Rules apply automatically when bank statements are uploaded
2. **Manual Trigger**: Click "Run Rules" button to apply to all existing transactions
3. **Processing Order**: Rules are applied in the order they appear (first match wins for pattern rules)
4. **Fallback**: If no rule matches, AI categorization is used

---

## Tips and Best Practices

1. **Start Simple**: Begin with basic pattern rules for categorization
2. **Test Incrementally**: Add rules gradually and test with "Run Rules"
3. **Order Matters**: Put more specific patterns before general ones
4. **Avoid Duplicates**: The system prevents duplicate linked transactions automatically
5. **Privacy**: `rules.json` is git-ignored, safe for personal patterns
6. **Use Examples**: Check `rules.example.json` and `rules.income-housing.example.json` for inspiration

---

## Example Files Available

- **`rules.example.json`**: Common purchases, subscriptions, transport, dining
- **`rules.income-housing.example.json`**: Income, rent, mortgage, insurance, healthcare
