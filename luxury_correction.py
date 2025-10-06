
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
    
    3. Generate a corrected luxury product title using official naming conventions:
       - Handbags: Brand → Style → Size → Color → Material → Subcategory
       - Shoes: Brand → Style → Size → Color → Material → Subcategory
       - Watches: Brand → Style → Model Name → Model Reference Number → Dial Color → Case Material → Gemstone → Gender → Wristwatch → Case Diameter
       - Fine Jewelry: Brand → Style → Serial Number → Movement → Dial Color → Material → Gender → Category → Case Size
    
    4. Important rules:
       - Always expand the material to its **full official name**
         (e.g., "Clemence" → "Taurillon Clémence Leather", "Togo" → "Togo Calfskin Leather").
       - Color normalization:
         - Extract all colors appearing in the title.
         - If more than 3 distinct colors are mentioned → use "Multicolor".
         - If 3 or fewer colors are mentioned → list them separated by commas, preserving order (e.g., "Black, Beige, Gold").
         - Use only official luxury color names from the provided list.
         - If no valid color is detected → use null
       - If the material is missing, infer the most likely luxury material.
       - Normalize subcategories:
         - Use the most specific **subcategory/type** if it is evident from the product title.
         - If no specific type is evident, use the main subcategory.
    
    5. Handbag Subcategory/Type Selection:
       - Main subcategories: Totes, Belt Bags, Backpacks, Clutches, Crossbody Bags, Shoulder Bags, Satchels, Luggage & Travel, Wallets
       - Secondary/specific types: Beach, Fanny Pack, Bucket Backpack, Wristlet, Messenger, Hobo, Top Handle Bags, Suitcases, Card Holder, Shopper, Mini Backpacks, Bucket Bag, Saddle, Duffel Bag, Coin Purse, Mini Bag, Briefcases, Long Wallet, Sling Bag, Make-up Bag, Bifold, Laptop Bag, Wallet on Chain, Diaper Bag, Gym Bag
       - Examples:
         - If the title contains “Mini Bag” → use subcategory “Mini Bag”
         - If the title contains “Bucket” → use subcategory “Bucket Bag”
         - If the title contains “Wallet on Chain” → use subcategory “Wallet on Chain”
         - If no specific type is present, fall back to the main subcategory.
    
    6. Size normalization logic:
    
    ### Louis Vuitton
    - Nano / Micro → XS
    - PM → S
    - MM → M
    - GM → L
    - If descriptive words appear like “high sized”, “small”, “large”, or “mini”, map approximately:
      - Mini / Nano / Micro / Tiny → XS
      - Small / PM → S
      - Medium / MM → M
      - Large / Big / GM / High Sized → L
    - Always return the **Generic Size (XS/S/M/L)**.
    
    ### Goyard
    - Mini → XS
    - PM → S
    - MM → M
    - GM → L
    - Always return the **Generic Size (XS/S/M/L)**.
    
    ### Hermès
    For Hermès, normalize size depending on the **style name**. **Always return the exact size label** as listed:
    
    Picotin:
    - Micro → Micro
    - 18 → 18
    - 22 → 22
    - 26 → 26
    
    Constance:
    - Micro 14 → Micro 14
    - Mini 18 → Mini 18
    - 24 → 24
    - Elan → Elan
    - To Go Wallet → To Go Wallet
    - Long Wallet → Long Wallet
    - Slim Wallet → Slim Wallet
    
    Lindy:
    - Mini 20 → Mini 20
    - 26 → 26
    - 30 → 30
    - 34 → 34
    
    Evelyne:
    - TPM 16 → TPM 16
    - PM 29 → PM 29
    - GM 33 → GM 33
    - TPM 40 → TPM 40
    
    Herbag:
    - 20 Mini → 20 Mini
    - 31 → 31
    - 39 → 39
    - Cabine → Cabine
    
    Jypsiere:
    - Mini → Mini
    - 28 → 28
    - 31 → 31
    - 34 → 34
    - 37 → 37
    
    Bride-a-Brac:
    - Small → Small
    - Large → Large
    
    Jige:
    - Duo Mini → Duo Mini
    - Elan 29 → Elan 29
    
    24/24:
    - 21 Mini → 21 Mini
    - 29 → 29
    - 35 → 35
    
    Bolide:
    - 20 Mini → 20 Mini
    - 27 → 27
    - 31 → 31
    - 35 → 35
    - 45 → 45
    
    Garden Party:
    - 30 → 30
    - 36 → 36
    
    Roulis:
    - Mini 18 → Mini 18
    - 23 → 23
    
    Verrou:
    - Mini Chaine → Mini Chaine
    - 23 → 23
    
    Della Cavalleria:
    - Mini → Mini
    
    Geta:
    - One Size → One Size
    
    In The Loop:
    - 18 → 18
    - 23 → 23
    
    Hac a Dos:
    - PM → PM
    - GM → GM
    
    Important: **Do not convert Hermès sizes to numeric-only or XS/S/M/L. Always use the exact label.**
    
    7. Reference data:
    
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
      "corrected_title": "Final corrected title with normalized size and subcategory"
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

        # Size mapping
        size_map = {"PM": "18", "MM": "22", "GM": "30"}
        if attrs.get("size") in size_map:
            attrs["size"] = size_map[attrs["size"]]

        # Update corrected title too
        corrected_title = result_json.get("corrected_title", "")
        for k, v in size_map.items():
            corrected_title = corrected_title.replace(f" {k}", f" {v}")
        corrected_title = corrected_title.replace("Handbag", "Shoulder Bag")
        corrected_title = corrected_title.replace("Bucket Bag", "Shoulder Bag")

        result_json["corrected_title"] = corrected_title
        result_json["attributes"] = attrs

    return result_json
