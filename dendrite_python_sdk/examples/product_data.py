import os
import asyncio
import time
from typing import Any, List, Optional
from pydantic import BaseModel, Field

from dendrite_python_sdk import DendriteRemoteBrowser
from dotenv import load_dotenv, find_dotenv

from dendrite_python_sdk.ai_util.generate_text import async_openai_request
from dendrite_python_sdk.ai_util.response_extract import extract_json
from dendrite_python_sdk.dendrite_browser.DendritePage import DendritePage
from dendrite_python_sdk.models.LLMConfig import LLMConfig


load_dotenv(find_dotenv())


class EcommerceRequest(BaseModel):
    url: str


# This may include things like price, tax, shipping cost, shipping options (e.g. Amazon prime, 3day shipping), product variants (size with options S, M, L or color with options blue, red, white), etc.


class PriceData(BaseModel):
    price: str = Field(..., description="Include the currency inside the response.")
    currency: str = Field(..., description="e.g USD")
    currencyRaw: str = Field(..., description="e.g $")


class ProductData(BaseModel):
    product_name: str = Field("The name of the product")
    # product_description: str = Field(
    #     ...,
    #     description="Get any text that describes the product. Often time this is under 'about product' or similar. Normally at least a paragraph long.",
    # )
    # product_image_urls: list[str] = Field(
    #     ...,
    #     description="Make sure you get the images you get the large display images and not any smaller ones. They are usually front and center next to the title.",
    # )
    # shipping_details: Optional[str] = Field(
    #     ...,
    #     description="Please list all information regarding shipping cost, shipping options (e.g. Amazon prime, 3day shipping) if available on the page.",
    # )

    original_price: str = Field(
        ...,
        description="e.g 1099,00. It should be the original price of the product. If only one price is listed, use it.",
    )
    sales_price: str = Field(
        ...,
        description="e.g 1099,00. It should be the current price of the product, even if there is a sale.",
    )
    # currencyRaw: str = Field(..., description="e.g '$'")
    # availability: Optional[bool] = Field(..., description="Is the item in stock or not")
    # available_colors: list[str] = Field(
    #     ...,
    #     description="Please list the colors that are available for this product if applicable.",
    # )
    current_variant: Optional[str] = Field(
        None,
        description="If a product has several 'variants' such as color, please list the current product variant's color or theme as a string if it is available on the page. This is usually only relevant for clothing items. E.g 'blue' if this is the current color.",
    )
    available_sizes: Optional[list[str]] = Field(
        [],
        description="Get all the available sizes that are selectable on the product page as a list of strings. This value is optional and usually only relevant for clothing items. Sometimes these are found inside size dropdowns. I only want the sizes that are currently available, often times unavailable sizes are greyed out, marked as out of stock or similar. It's important that you only get the currently available sizes that aren't hidden.",
    )
    # unavailable_sizes: list[str] = Field(
    #     [],
    #     description="Get all the unavailable sizes as a list of strings. I only want the sizes that are currently unavailable, often times unavailable sizes are greyed out or similar.",
    # )


class EcommerceResponse(BaseModel):
    variants: List[ProductData]


async def extract_data(
    page: DendritePage,
    propery_name: str,
    propery_schema: Any,
):
    print(f"Extracting {propery_name}")
    try:
        res = await page.scrape(
            f"Please extract the data with the following json schema: {propery_schema}. Create a script should return a value that matches the json schema's `type`.",
            return_data_json_schema=propery_schema,
        )
        print(
            f"\n\n\nRes for '{propery_name}' with schema {propery_schema}: ",
            res.json_data,
            "\n\nThis is the message: '",
            res.message,
            "'\n\nGenerated script:",
            res.created_script,
        )
        return propery_name, res.json_data
    except Exception as e:
        print("Error extracting data: ", e)

    return propery_name, None


async def extract_all(page: DendritePage, json_schema: Any):
    tasks = []
    for propery_name, propery_schema in json_schema["properties"].items():
        tasks.append(
            extract_data(
                page,
                propery_name,
                propery_schema,
            )
        )

    results = await asyncio.gather(*tasks)
    response_data = {}
    for res in results:
        response_data[res[0]] = res[1]

    print("extract_all response_data: ", response_data)
    return response_data


async def get_all_product_variants(
    page: DendritePage, browser: DendriteRemoteBrowser
) -> List[Any]:
    prompt = f"Hi, can you help me extract the element for selecting different product variants? These elements are often times small boxes with different colors or small previews of each product variant. Often times product variants are different colors for clothes, but it could be theme too or something else too. Don't extract the element for different size variants, only color or theme."

    variant_buttons = await page.get_interactions_selector(
        prompt=prompt, use_cache=False
    )
    print("variant_buttons: ", variant_buttons)

    results = []
    for el in variant_buttons:
        try:
            await el.get_playwright_locator().click(timeout=0)
            active_page = await browser.get_active_page()
            res = await extract_all(
                active_page,
                json_schema=ProductData.model_json_schema(),
            )
            results.append(res)
        except Exception as e:
            pass
    return results


async def extract_product_data(url: str) -> EcommerceResponse:
    dendrite_browser = DendriteRemoteBrowser(
        openai_api_key=os.environ.get("OPENAI_API_KEY", ""),
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
        dendrite_api_key=os.environ.get("DENDRITE_API_KEY", ""),
    )
    print(" launch: ", url)

    await dendrite_browser.launch()
    page = await dendrite_browser.goto(url, scroll_through_entire_page=False)

    product_variant_data = await get_all_product_variants(page, dendrite_browser)
    print("Found this many variants: ", len(product_variant_data))

    print("page_data_results: ", product_variant_data)

    return EcommerceResponse(variants=product_variant_data)


async def test(url: str):
    browser = DendriteRemoteBrowser(
        openai_api_key=os.environ.get("OPENAI_API_KEY", ""),
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
        dendrite_api_key=os.environ.get("DENDRITE_API_KEY", ""),
    )
    page = await browser.goto(url, scroll_through_entire_page=False)
    res = await page.scrape(
        "Get the price of the product please",
        use_cache=False,
    )
    print("res: ", res)


urls_to_test = [
    "https://shop.mango.com/us/en/p/women/dresses-and-jumpsuits/dresses/bow-wrap-dress_67095739",
    "https://www.warbyparker.com/eyeglasses/esme/aventurine-tortoise-with-polished-gold",
    "https://www.macys.com/shop/product/hippie-rose-juniors-seamless-cropped-tube-top?ID=17871317",
    "https://www.newegg.com/kingspec-4tb-2-5-sata/p/0D9-000D-00158?item=9SIB1V8JM85135&nm_mc=knc-googleadwords&cm_mmc=knc-googleadwords-_-solid+state+disk-_-kingspec-_-9SIB1V8JM85135&utm_source=google&utm_medium=organic+shopping&utm_campaign=knc-googleadwords-_-solid+state+disk-_-kingspec-_-9SIB1V8JM85135&source=region&srsltid=AfmBOopt4ppgjN2OTzE7OAKnfSnfkNmQBJR1CrKIIk-87vOlgdDiFHQJkkQ&com_cvv=d30042528f072ba8a22b19c81250437cd47a2f30330f0ed03551c4efdaf3409e",
    "https://shop.mango.com/us/en/p/women/dresses-and-jumpsuits/dresses/belt-shirt-dress_67085740",
    "https://us.shein.com/5pairs-Pointed-Cat-Eye-False-Eyelashes-p-10392442.html",
    "https://shop.mango.com/us/en/p/women/dresses-and-jumpsuits/dresses/ribbed-knit-dress-with-opening_67063264",
    "https://www.zara.com/us/en/embroidered-tied-top-p00881070.html",
    "https://www.newegg.com/g-skill-32gb-288-pin-ddr5-sdram/p/N82E16820374351",
    "https://www.zarahome.com/am/round-paper-coaster-pack-of-4-l42241550?ct=true&categoryId=1020261524&colorId=707",
    "https://us.princesspolly.com/products/emily-maxi-dress-pink-floral",
    "https://www.meshki.us/products/teddi-denim-mini-dress-mid-blue",
    "https://www.nike.com/t/air-max-90-futura-womens-shoes-kvRZ4h",
    "https://www.urbanoutfitters.com/shop/bdg-joey-poplin-wide-leg-pant",
    "https://shop.mango.com/us/en/p/women/dresses-and-jumpsuits/dresses/printed-satin-dress_57047736",
    "https://www.abercrombie.com/shop/wd/p/2-pack-essential-body-skimming-tees-53499347",
    "https://www.target.com/p/skyline-softside-large-checked-spinner-suitcase-gray-heather/-/A-89040545",
    "https://www.zarahome.com/do/en/medium-sized-wide-storage-jar-l49246428",
    "https://photo.walgreens.com/store/product-details?category=StoreCat_25657&sku=CommerceProduct_7184&com_cvv=d30042528f072ba8a22b19c81250437cd47a2f30330f0ed03551c4efdaf3409e",
    "https://www.shoporangetheory.com/ot-burn-5-0-c-otbeat-burn",
    "https://photo.walgreens.com/store/prints-information",
    "https://us.princesspolly.com/products/hugs-kisses-knit-maxi-skirt-red-curve",
    "https://shop.lululemon.com/p/tops-short-sleeve/Swiftly-Tech-SS-2/_/prod9750519",
    "https://www.pacsun.com/ps-%2F-la/bisou-xx-bisou-baby-t-shirt-0702512330465.html",
    "https://www.farfetch.com/shopping/women/7-for-all-mankind-luxe-denim-jumpsuit-item-22234133.aspx",
    "https://us.shein.com/SHEIN-Frenchy-Women-S-Solid-Color-Fringed-Sleeveless-Tank-Top-For-Summer-p-28177168.html",
    "https://onelink.shein.com/0/googlefeed_us?goods_id=28261457&lang=en&currency=USD&skucode=I913pocaeq62",
    "https://www.zara.com/us/en/printed-tulle-top-p03067035.html",
    "https://www.amazon.com/betadine/s?k=betadine",
    "https://www.pacsun.com/john-galt/black-leah-long-sleeve-top-0704601601007.html",
    "https://www.pacsun.com/pacsun/eco-black-bre-triangle-bikini-top-0810603590050001.html",
    "https://www.macys.com/shop/product/giani-bernini-small-polished-hoop-earrings-in-sterling-silver-25mm-created-for-macys?ID=11128719",
    "https://www.goat.com/sneakers/530-grey-matter-mr530cb",
    "https://shop.mango.com/us/en/p/women/dresses-and-jumpsuits/dresses/print-wrap-dress_67030464",
    "https://us.shein.com/Floral-Bikini-Set-Halter-Triangle-Bra-&-Wide-Strap-Side-Thong-Bottom-2-Western-Piece-Bathing-Suit-p-5978267.html",
    "https://shop.lululemon.com/p/womens-t-shirts/Swiftly-Tech-SS-2-MD/_/prod9940024",
    "https://www.meshki.us/products/lylah-denim-pocket-mini-skirt-mid-blue",
    "https://us.shein.com/Women's-Color-Block-Long-Sleeve-One-Piece-Swimsuit-p-29103778-cat-2191.html",
    "https://www.walgreens.com/store/c/avene-cicalfate--restorative-protective-cream/ID=300401867-product",
    "https://us.shein.com/Solid-Color-V-Neck-Side-Cross-Tie-One-Piece-Swimsuit-p-31081120.html",
    "https://www.walgreens.com/store/c/nature's-bounty-magnesium-500mg-value-size,-tablets/ID=prod6196331-product",
    "https://us.shein.com/Fashionable-And-Simple-One-Shoulder-Cross-Body-Bag-p-34472408.html",
    "https://www.levi.com/US/en_US/clothing/women/jeans/loose/low-pro-womens-jeans/p/A09640020",
    "https://shop.mango.com/us/en/p/women/dresses-and-jumpsuits/dresses/animal-print-textured-dress_67050461",
    "https://www.nike.com/t/dunk-low-lx-womens-shoes-16c9ld",
    "https://www.sephora.com/product/P506491?skuId=2689792",
    "https://www.abercrombie.com/shop/us/p/curve-love-high-rise-mom-short-55096825",
    "https://www.target.com/p/women-39-s-perfectly-cozy-pullover-sweatshirt-stars-above-8482-light-gray-s/-/A-77775338",
    "https://us.shein.com/SHEIN-VCAY-Leaf-Plaid-Print-Wide-Strap-Top-Wide-Leg-Pants-p-19638657-cat-1780.html?mallCode=1",
    "https://shop.mango.com/us/en/p/women/dresses-and-jumpsuits/dresses/flared-corset-dress_57020462",
    "https://www.amazon.com/Schick-Multipurpose-Exfoliating-Dermaplaning-Precision/dp/B0787GLBMV",
    "https://m.shein.com/roe/2pcs-set-Faux-Pearl-Decor-Waist-Chain-p-14471835.html",
    "https://onelink.shein.com/0/googlefeed_us?goods_id=4412006&lang=en&currency=USD&skucode=I01swi5b4aak",
    "https://us.princesspolly.com/products/billini-novena-boot-white",
    "https://www.anthropologie.com/shop/by-anthropologie-button-front-halter-swing-blouse",
    "https://www.abercrombie.com/shop/us/p/tailored-wide-leg-pants-51625331",
    "https://www.shein.com/Faux-Pearl-Decor-Flip-Cover-Square-Bag,-Woven-Straw-Crossbody-Bag-Small-Handbag-p-16521889-cat-2150.html",
    "https://www.walgreens.com/store/c/productlist/N=537-2999951453-3000007703",
    "https://www.target.com/p/women-39-s-perfectly-cozy-pullover-sweatshirt-stars-above-8482-dark-gray-l/-/A-77774586",
    "https://www.walgreens.com/store/c/nyx-professional-makeup-retractable-long-lasting-mechanical-lip-liner/ID=300422852-product",
    "https://retrofete.com/products/isadora-embellished-dress-mltbl",
    "https://www.zara.com/us/en/porcelain-dessert-plate-with-antique-finish-rim-p45270202.html",
    "https://www.newegg.com/samsung-1tb-980-pro/p/N82E16820147790",
    "https://www.nike.com/t/court-legacy-little-kids-shoes-Mb7npn/DA5381-102?nikemt=true&srsltid=AfmBOorBvcKiKsRwHptJDIXIaVm2d_GuXfy5sQmHBZ9Qh_mmcmOlLrROwXA",
    "https://www.target.com/p/l-39-oreal-paris-true-match-lumi-glotion-natural-glow-enhancer-901-fair-glow-1-35-fl-oz/-/A-52437712",
    "https://us.princesspolly.com/products/matilda-maxi-set-green",
    "https://www.target.com/p/women-39-s-perfectly-cozy-lounge-jogger-pants-stars-above-8482-dark-gray-m/-/A-77774603",
    "https://us.princesspolly.com/products/fall-maxi-skirt-taupe",
    "https://www.abercrombie.com/shop/us/p/premium-polished-tee-54378330",
    "https://retrofete.com/products/ada-jacket-fdbtr",
    "https://us.shein.com/SHEIN-Priv-Cut-Out-Split-Thigh-Cami-Dress-p-16542558.html?mallCode=1",
    "https://us.shein.com/Summer-Beach-Solid-Color-Textured-Halter-Neck-Split-Swimwear-p-32019947.html",
    "https://apps.apple.com/gr/app/eq-health/id1565763664",
    "https://www.thereformation.com/products/bethany-ballet-flat/1312478.html",
    "https://www.zarahome.com/by/en/cutlery-set-with-handle-detail-l48220311",
    "https://www.pacsun.com/pacsun/pacific-sunwear-rolled-sweat-shorts-5963525.html",
    "https://www.abercrombie.com/shop/us/p/crochet-style-maxi-dress-53806825",
    "https://www.walgreens.com/store/c/colgate-optic-white-charcoal-whitening-toothpaste-cool-mint/ID=300410663-product",
    "https://us.shein.com/Flap-Pocket-Drop-Shoulder-Crop-Corduroy-Jacket-p-24029984-cat-1776.html",
    "https://www.cos.com/en/men/menswear/t-shirts/product.heavy-duty-t-shirt-yellow.1147848010.html",
    "https://us.princesspolly.com/products/channing-lace-mini-dress-pink",
    "https://us.shein.com/Faux-Pearl-Decor-Stud-Earrings-p-11719936-cat-4099.html",
    "https://www.madewell.com/denim-lady-jacket-in-lakecourt-wash-NQ450.html",
    "https://www.eu.lululemon.com/en-se/p/dance-studio-high-rise-short-3.5%22/153000535.html",
    "https://www.abercrombie.com/shop/us/p/tailored-wide-leg-pants-51625331",
    "https://www.abercrombie.com/shop/wd/p/2-pack-essential-body-skimming-tees-53499347",
    "https://www.pacsun.com/pacsun/jennifer-sweater-tank-top-0740508520108.html",
    "https://shop.mango.com/us/en/p/women/skirts/short/leather-effect-culottes_67070472",
    "https://www.walgreens.com/store/c/productlist/N=263-2999951495",
    "https://www.abercrombie.com/shop/us/p/plunge-cowl-back-maxi-dress-55283320",
    "https://www.target.com/p/women-39-s-cali-flip-flop-sandals-shade-38-shore-8482/-/A-89382005",
    "https://www.zara.com/us/en/embroidered-tied-top-p00881070.html",
    "https://www.apple.com/shop/buy-iphone/iphone-15/6.7-inch-display-256gb-black-unlocked",
    "https://www.abercrombie.com/shop/wd/p/2-pack-essential-body-skimming-tees-53499347",
    "https://us.shein.com/3pack-Seamless-Panty-Set-p-2245474.html",
    "https://www.ikea.com/us/en/p/spruttig-hanger-black-20317079/",
]


asyncio.run(
    extract_product_data(
        urls_to_test[10]
        # "https://www.amazon.com/Redragon-S101-Keyboard-Ergonomic-Programmable/dp/B00NLZUM36/ref=sr_1_3?_encoding=UTF8&content-id=amzn1.sym.12129333-2117-4490-9c17-6d31baf0582a&dib=eyJ2IjoiMSJ9.xPISJOYMxoc_9dHbx858fxwpXnhNZrtv8JW5ZP3BaCjqaHIK38QAFzAsY9vAczkOx_jT47M5saeEynDwm1y20BOqIUbVycKgrgWhsv3MCsvpEd57g5uZRNzYwHS9Aw2obI3MPmxewiD3kqCeZDfRh69TGNH_g8luFs-XZxYXIBD2JVQ9pYTQA6VM4k06p7kUjdUQzbe1NHHkPD6bd_mILwz7PFE_rYcpXnDqkLtMtSY.LORYuOmHcSqhnVbbYz8QsC5kxdeESOXcjd_PCPjpzMs&dib_tag=se&keywords=gaming%2Bkeyboard&pd_rd_r=64dc3a90-64a6-40b9-b7a1-2d68d3ecc3b4&pd_rd_w=x25KJ&pd_rd_wg=OZzqF&pf_rd_p=12129333-2117-4490-9c17-6d31baf0582a&pf_rd_r=HP8K759Y8NJCW8Z9C275&qid=1719487385&sr=8-3&th=1"
        # "https://www.amazon.com/Portable-Mechanical-Keyboard-MageGee-Backlit/dp/B098LG3N6R/ref=sr_1_2?_encoding=UTF8&content-id=amzn1.sym.12129333-2117-4490-9c17-6d31baf0582a&dib=eyJ2IjoiMSJ9.xPISJOYMxoc_9dHbx858fxwpXnhNZrtv8JW5ZP3BaCjqaHIK38QAFzAsY9vAczkOx_jT47M5saeEynDwm1y20JZ85TVB8YZ7cwvsm0LDrBK1PUvuJ-xGXkNcVHVIhrQc9kBmR5169dJ6bjz3i9LTKih1i1gw9zMA5shlsZn0KaVLU1EJAlCk2vS5bmQ5Idk0jdUQzbe1NHHkPD6bd_mIL2J7EUeyr51zzG5sIHNZF8s.0rZvfrTY0gQfCCR3e3ZG37IngUeL9TvLAKFP0uxXQm8&dib_tag=se&keywords=gaming%2Bkeyboard&pd_rd_r=a3b11a83-7bdf-42ad-8ccc-850a2a9be0ae&pd_rd_w=thyAn&pd_rd_wg=QuR3V&pf_rd_p=12129333-2117-4490-9c17-6d31baf0582a&pf_rd_r=EGJ9WE3PH43XY2VRNXYS&qid=1719385097&sr=8-2&th=1"
    )
)

# Session ID "get product data variants" + domain to create key  - get ID after run

# Learn:
# 1. Click all variants (expected value check)
# 2. Scrape the relevant data from each one
# 3. Aggrigate generated code


# Run:
# Interact Click all the product variants
# Create interaction script


# Find element - look at page
# Inspect html
# Confirm

# Today:
# Store variant locator (what if different ones?) and get instantly
# Cache extraction scripts
# Set up endpoint
# Nice endpoint: id give train sample -> test sample -> run
