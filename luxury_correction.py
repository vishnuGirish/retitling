
import os
import json
import re
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# ==========================
# 1. Configure Gemini API
# ==========================
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

genai.configure(api_key=api_key)




# ==========================
# 2. Reference Data
# ==========================
luxury_data = {
    "brands": ["Louis Vuitton", "Hermes", "Chanel", "Gucci", "Prada", "Fendi", "Dior", "Saint Laurent",
               "Bottega Veneta", "Celine", "Balenciaga", "Loewe", "Goyard", "Burberry", "Rolex", "Omega", "Cartier"],
    "sizes": ["PM", "MM", "GM", "Small", "Medium", "Large", "Mini", "Maxi", "Jumbo", "XS", "S", "M", "L", "XL"],
    "colors": ["Black", "White", "Brown", "Red", "Blue", "Green", "Pink", "Purple", "Yellow", "Orange",
               "Grey", "Gray", "Beige", "Tan", "Cream", "Navy", "Burgundy", "Bordeaux", "Cognac", "Nude", "Taupe", "Multicolor"],
    "materials": ["Leather", "Canvas", "Suede", "Patent", "Calfskin", "Lambskin", "Caviar", "Saffiano",
                  "Nappa", "Intrecciato", "Vernis", "Epi", "Togo", "Clemence"],
    "handbag_subcategories": ["Bag", "Backpack", "Clutch", "Tote", "Wallet", "Card Holder", "Top Handle Bag",
                               "Crossbody Bag", "Shoulder Bag", "Handbag", "Purse"],
    "shoe_subcategories": ["Sneakers", "Boots", "Loafers", "Heels", "Sandals", "Flats", "Mules", "Oxfords"],
    "jewelry_subcategories": ["Ring", "Necklace", "Bracelet", "Earrings", "Brooch", "Cufflinks"],
    "watch_subcategories": ["Wristwatch"]
}

# ==========================
# 3. Luxury Title Correction + Post Processing
# ==========================
def correct_luxury_title(product_title: str) -> dict:
    """
    Uses Gemini 2.5 to detect category, extract structured attributes,
    and generate a corrected luxury title.
    Also applies post-processing:
    - Replace "Handbag"/"Bucket Bag" with "Shoulder Bag"
    - Convert PM/MM/GM sizes to numeric values
    """
    prompt = f"""
    You are an expert in luxury fashion products: Handbags, Shoes, Watches, and Fine Jewelry.
    
    Your task:
    1. Detect the product category.
    2. Extract structured attributes as JSON:
       brand, style, size, color, material, subcategory, model_name, model_reference_number,
       dial_color, case_material, gender, case_diameter.
       Use null if missing.
    
    3. Generate a corrected luxury product title using **official naming conventions**:

    ### Handbags:
    Format → Brand → Style → Size → Color → Material → Subcategory → always end with "Bag" if missing

    ### Shoes:
    Format → Brand → Style → Size → Color → Material → Subcategory

    ### Watches:
    Format → Brand → Style → Model Name → Model Reference Number → Movement → Chronograph (if applicable) → Dial Color → Case Material → Gemstone → Gender → Wristwatch → Case Diameter
    - The word **“Chronograph”** must appear **after the movement**, not next to the style.
        Example: `IWC Aquatimer IW376805 Automatic Chronograph Black Dial Stainless Steel Men's Wristwatch 44mm`
    - **Do not include “and”** between materials such as "Stainless Steel" and "Yellow Gold".
        Example: `Jaeger-LeCoultre Reverso Classique 261.5.08 Silver Dial Stainless Steel 18k Yellow Gold Women's Wristwatch 20mm`

    ### Fine Jewelry:
    Format → Brand → Style → Serial Number → Movement → Dial Color → Material → Gender → Category → Case Size
    
    4. Important rules:
       - Always expand the material to its **full official name** (e.g., "Clemence" → "Taurillon Clémence Leather", "Togo" → "Togo Calfskin Leather").
       - Color normalization:
         - Extract all colors appearing in the title.
         - If more than 3 distinct colors are mentioned → use "Multicolor".
         - If 3 or fewer colors are mentioned → list them separated by commas, preserving order (e.g., "Black, Beige, Gold").
         - Avoid repeating "Multicolor" or any color.
         - Use only official luxury color names from the provided list.
         - If no valid color is detected → use null
       - If the material is missing, infer the most likely luxury material.
       - Normalize subcategories:
         - Use the most specific **subcategory/type** if evident from the product title.
         - If no specific type is evident, use the main subcategory.
         - For handbags, always ensure "Bag" is at the end.
        - Don't repeat the same word twice in the title
        - The language must be English only — replace any special characters with their correct English letters (e.g., é → e, @ → a, > → g)
    
    5. Handbag Subcategory/Type Selection:
       - Main subcategories: Totes, Belt Bags, Backpacks, Clutches, Crossbody Bags, Shoulder Bags, Satchels, Luggage & Travel, Wallets
       - Secondary/specific types: Beach, Fanny Pack, Bucket Backpack, Wristlet, Messenger, Hobo, Top Handle Bags, Suitcases, Card Holder, Shopper, Mini Backpacks, Bucket Bag, Saddle, Duffel Bag, Coin Purse, Mini Bag, Briefcases, Long Wallet, Wallet on Chain, Diaper Bag, Gym Bag
       - Examples:
         - If the title contains “Mini Bag” → use subcategory “Mini Bag”
         - If the title contains “Bucket” → use subcategory “Bucket Bag”
         - If the title contains “Wallet on Chain” → use subcategory “Wallet on Chain”
         - If no specific type is present, fall back to the main subcategory.
    
    6. Size normalization logic:
    
    ### Louis Vuitton
    - strictly use PM, MM, GM for size if it is in title for Louis Vuitton items.
    - Nano / Micro → XS, PM → S, MM → M, GM → L
    - Map descriptive words: Mini/Nano → XS, Small/PM → S, Medium/MM → M, Large/GM → L
    - Return **Generic Size (XS/S/M/L)** for internal attributes but maintain PM/MM/GM in corrected title.
    
    ### Hermes
    - Sizes for Hermes should remain exact as per style (Picotin, Constance, Lindy, Evelyne, Herbag, Jypsiere, Bride-a-Brac, Jige, 24/24, Bolide, Garden Party, Roulis, Verrou, Della Cavalleria, Geta, In The Loop, Hac a Dos)
    - **Do not convert Hermès sizes to XS/S/M/L. Use exact label.**
    
    7. Watches
    - Extract model info from **reference number**, not title.
    - Include dial color if available.
    - Correct gender based on reference number, not title.
    
    8. Reference data:
    
    Brands: {', '.join(luxury_data['brands'])}
    Sizes: {', '.join(luxury_data['sizes'])}
    Colors: {', '.join(luxury_data['colors'])}
    Materials: {', '.join(luxury_data['materials'])}
    Handbag subcategories: {', '.join(luxury_data['handbag_subcategories'])}
    Shoe subcategories: {', '.join(luxury_data['shoe_subcategories'])}
    Jewelry subcategories: {', '.join(luxury_data['jewelry_subcategories'])}
    Watch subcategories: {', '.join(luxury_data['watch_subcategories'])}
    
    Input title: "{product_title}"
    
    Return a single JSON object:
    {{
      "detected_category": "category",
      "attributes": {{
          "brand": "value or null",
          "style": "value or null",
          "size": "Hermès exact label or Generic Size (XS/S/M/L) or null",
          "color": "value or null",
          "material": "value or null",
          "subcategory": "most appropriate subcategory/type or null",
          "model_name": "value or null",
          "model_reference_number": "value or null",
          "dial_color": "value or null",
          "case_material": "value or null",
          "gender": "value or null",
          "case_diameter": "value or null"
      }},
      "corrected_title": "Final corrected title with normalized size, subcategory, 'Bag' suffix, and color deduplication"
    }}
    """



    model = genai.GenerativeModel("gemini-2.5-pro")
    response = model.generate_content(prompt)

    result_text = response.text.strip()
    try:
        result_json = json.loads(result_text)
    except:
        match = re.search(r'\{.*\}', result_text, re.DOTALL)
        if match:
            result_json = json.loads(match.group(0))
        else:
            result_json = {"error": "Failed to parse Gemini response", "raw_response": result_text}
            return result_json

    # ==========================
    # Post Processing
    # ==========================
    if "attributes" in result_json:
        attrs = result_json["attributes"]

        # Subcategory normalization
        if attrs.get("subcategory"):
            if attrs["subcategory"].lower() in ["handbag", "bucket bag", "Top Handle Bag"]:
                attrs["subcategory"] = "Shoulder Bag"


        # Update corrected title too
        corrected_title = result_json.get("corrected_title", "")

        corrected_title = corrected_title.replace("Handbag", "Shoulder Bag")
        corrected_title = corrected_title.replace("Bucket Bag", "Shoulder Bag")

        result_json["corrected_title"] = corrected_title
        result_json["attributes"] = attrs

    return result_json
