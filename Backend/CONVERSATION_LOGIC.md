# Smart Conversational Follow-up Logic

## Problem Solved

**Before:** When users asked for "cheaper" then "more expensive" options, the system would compare against the cheaper results, leading to confusing responses:

```
User: "show me laptop under 1 Lakh" → Shows laptops at 70k
User: "show cheaper"                → Shows laptops at 49k
User: "show more expensive"         → Shows laptops at 63k ❌ (user expected 90k+)
```

**After:** The system now intelligently tracks the original search and uses it as reference when appropriate:

```
User: "show me laptop under 1 Lakh" → Shows laptops at 70k (saved as ORIGINAL)
User: "show cheaper"                → Shows laptops at 49k
User: "show more expensive"         → Shows laptops at 90k+ ✅ (references ORIGINAL)
```

## How It Works

### 1. Original Search Tracking

When a user starts a NEW search (not a follow-up), the system saves these results as the "original" reference:

```python
# User searches: "show me laptop under 1 Lakh"
products = search_products(...)
rag_pipeline.original_search_results = products[:5]  # Saved
rag_pipeline.last_search_results = products[:5]       # Also saved for immediate follow-ups
```

### 2. Smart Reference Selection

When handling follow-ups, the system decides which reference to use:

```python
# If user asks for "more expensive" AFTER asking for "cheaper"
# → Use ORIGINAL reference (not the cheaper results)

if (query contains "more expensive") AND 
   (last query was "cheaper") AND
   (original results exist):
    reference = original_search_results  # Smart!
else:
    reference = last_search_results      # Normal behavior
```

### 3. Topic Change Detection

When the user switches to a different product type, the original context is cleared:

```python
# User was searching for laptops
last_type = "laptop"

# User now searches: "show me keyboard"
current_type = "keyboard"

if last_type != current_type:
    rag_pipeline.original_search_results = []  # Clear old context
```

## Conversation Examples

### Example 1: Smart Price Navigation

```
1. User: "show me laptop under 1 Lakh taka"
   → Bot: [Shows Tecno Megabook 70k, Lenovo 79k, etc.]
   📌 Stores as ORIGINAL

2. User: "show me cheaper alternatives"
   → Bot: [Shows ASUS Vivobook 49k, Lenovo Slim 49k, etc.]
   → References: ORIGINAL (70k laptops)
   → Result: Cheaper laptops around 49k ✅

3. User: "show me more expensive options"
   → Bot: [Shows laptops at 90k+, not 63k]
   → Smart Detection: Last query was "cheaper", so use ORIGINAL reference
   → References: ORIGINAL (70k laptops), NOT last results (49k)
   → Result: More expensive laptops 90k-120k ✅

4. User: "show me even more expensive"
   → Bot: [Shows laptops at 150k+]
   → References: LAST results (90k+ laptops)
   → Result: Even more expensive laptops ✅
```

### Example 2: Topic Change

```
1. User: "show me gaming laptop"
   → Bot: [Shows gaming laptops 80k-150k]
   📌 Stores as ORIGINAL (type: laptop)

2. User: "show me keyboard under 2000"
   → Detection: New topic (keyboard ≠ laptop)
   → Action: Clear original laptop results
   → Bot: [Shows keyboards under 2000৳]
   📌 Stores as ORIGINAL (type: keyboard)

3. User: "show me more expensive options"
   → Bot: [Shows more expensive KEYBOARDS, not laptops]
   → References: Current keyboard context ✅
```

### Example 3: Continuous Follow-ups

```
1. User: "show me laptop under 50000"
   → Bot: [Shows laptops ~40-50k]
   📌 Original: 40-50k range

2. User: "cheaper"
   → Bot: [Shows laptops ~30k]
   → References: Original (40-50k)

3. User: "even cheaper"
   → Bot: [Shows laptops ~25k]
   → References: Last (30k)
   → Normal behavior, going progressively cheaper ✅

4. User: "more expensive"
   → Bot: [Shows laptops ~40-50k area]
   → Smart Detection: Uses ORIGINAL reference
   → Back to original price range ✅
```

## Implementation Details

### Data Structures

```python
class ProductRAGPipeline:
    def __init__(self):
        self.last_search_results = []      # Most recent results (any query)
        self.original_search_results = []  # First non-follow-up search results
        self.conversation_memory = []       # Last 10 queries and responses
```

### Key Functions

1. **`handle_follow_up_query()`**
   - Determines if ORIGINAL reference should be used
   - Checks conversation history for "cheaper" → "more expensive" pattern
   - Filters products already shown

2. **`search_products_for_voice_agent()`**
   - Detects follow-up vs new search
   - Stores original results for new searches
   - Clears original when topic changes

3. **`get_product_type()`**
   - Identifies product category (laptop, keyboard, desktop, etc.)
   - Used for topic change detection
   - Excludes accessories and components

## Benefits

✅ **More Intuitive:** Users get expected results when navigating prices  
✅ **Context Aware:** System remembers the original context  
✅ **Topic Switching:** Cleanly handles changing product types  
✅ **No Repetition:** Avoids showing same products multiple times  
✅ **Natural Flow:** Conversations feel more human-like  

## Testing

Run the test script to verify smart behavior:

```bash
source ../venv/bin/activate
python test_conversation.py
```

Expected output:
- Test 1: Initial laptop search → ~70k range
- Test 2: Cheaper → ~49k range  
- Test 3: More expensive → **~90k+ range** (not 63k!)
- Test 4: Even more expensive → ~120k+ range
- Test 5: Keyboard search → Keyboards (context switched)
- Test 6: More expensive → More expensive keyboards (stays in keyboard context)

## Future Improvements

Potential enhancements:
- Track multiple reference points (original, last, second-to-last)
- Support "go back" command to return to original results
- Remember price ranges across sessions
- Support "similar to the first one" references
