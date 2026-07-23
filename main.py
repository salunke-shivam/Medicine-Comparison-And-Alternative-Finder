import os
import requests
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_community.tools import DuckDuckGoSearchRun
from langgraph.graph import StateGraph, END
from typing import TypedDict

load_dotenv()

# setup groq
llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model_name="openai/gpt-oss-20b"
)

# setup duckduckgo search
search_tool = DuckDuckGoSearchRun()


# this holds all the data as it moves through the graph
class MedicineState(TypedDict):
    medicine_name: str
    fda_data: str
    rxnorm_data: str
    composition_data: str
    indian_price_data: str
    search_data: str
    final_output: str


# step 1 - get medicine info from openfda
def get_fda_info(state: MedicineState):
    medicine = state["medicine_name"]
    print(f"\n Searching FDA database for: {medicine}")

    try:
        url = f"https://api.fda.gov/drug/label.json?search=openfda.brand_name:{medicine}&limit=1"
        response = requests.get(url, timeout=10)
        data = response.json()

        if "results" in data:
            result = data["results"][0]

            description = result.get("description", ["Not available"])[0]
            purpose = result.get("purpose", ["Not available"])[0]
            warnings = result.get("warnings", ["Not available"])[0]

            fda_info = f"""
            FDA Information for {medicine}:
            Description: {description[:500]}
            Purpose: {purpose[:300]}
            Warnings: {warnings[:300]}
            """
        else:
            fda_info = f"No FDA data found for {medicine}"

    except Exception as e:
        fda_info = f"Could not get FDA data: {str(e)}"

    return {"fda_data": fda_info}


# step 2 - get rxnorm id and alternatives
def get_rxnorm_alternatives(state: MedicineState):
    medicine = state["medicine_name"]
    print(f"\n Searching RxNorm for alternatives to: {medicine}")

    try:
        url = f"https://rxnav.nlm.nih.gov/REST/rxcui.json?name={medicine}"
        response = requests.get(url, timeout=10)
        data = response.json()

        rxcui = None
        if "idGroup" in data and "rxnormId" in data["idGroup"]:
            rxcui = data["idGroup"]["rxnormId"][0]

        if rxcui:
            alt_url = f"https://rxnav.nlm.nih.gov/REST/rxclass/relatedByClass.json?rxcui={rxcui}&relaSource=ATC&classTypes=CHEMICAL"
            alt_response = requests.get(alt_url, timeout=10)
            alt_data = alt_response.json()

            alternatives_list = []
            if "relatedByClassCollection" in alt_data:
                items = alt_data["relatedByClassCollection"].get("rxclassDrugInfoList", {})
                drug_info = items.get("rxclassDrugInfo", [])
                for item in drug_info[:5]:
                    name = item.get("minConcept", {}).get("name", "")
                    if name:
                        alternatives_list.append(name)

            if alternatives_list:
                rxnorm_info = f"RxNorm ID: {rxcui}\nRelated medicines: {', '.join(alternatives_list)}"
            else:
                rxnorm_info = f"RxNorm ID: {rxcui}\nNo related medicines found"
        else:
            rxnorm_info = f"Could not find RxNorm ID for {medicine}"

    except Exception as e:
        rxnorm_info = f"Could not get RxNorm data: {str(e)}"

    return {"rxnorm_data": rxnorm_info}


# step 3 - get the composition of the medicine
def get_composition(state: MedicineState):
    medicine = state["medicine_name"]
    print(f"\n Getting composition details for: {medicine}")

    try:
        url = f"https://api.fda.gov/drug/label.json?search=openfda.brand_name:{medicine}&limit=1"
        response = requests.get(url, timeout=10)
        data = response.json()

        if "results" in data:
            result = data["results"][0]

            active = result.get("active_ingredient", ["Not available"])[0]
            inactive = result.get("inactive_ingredient", ["Not available"])[0]
            dosage = result.get("dosage_and_administration", ["Not available"])[0]

            composition_info = f"""
            Composition of {medicine}:
            Active Ingredients: {active[:500]}
            Inactive Ingredients: {inactive[:300]}
            Dosage Info: {dosage[:300]}
            """
        else:
            print(f" FDA composition not found, searching internet...")
            query = f"{medicine} active ingredients composition"
            result = search_tool.run(query)
            composition_info = f"Composition from web:\n{result[:1000]}"

    except Exception as e:
        composition_info = f"Could not get composition: {str(e)}"

    return {"composition_data": composition_info}


# step 4 - get indian prices from multiple pharmacy sites
def get_indian_price(state: MedicineState):
    medicine = state["medicine_name"]
    print(f"\n Searching Indian pharmacy prices for: {medicine}")

    all_price_info = ""

    # search 1mg price
    try:
        print("   Checking 1mg.com...")
        query_1mg = f"site:1mg.com {medicine} price MRP India rupees"
        result_1mg = search_tool.run(query_1mg)
        all_price_info += f"""
        1mg.com Price Results:
        {result_1mg[:600]}
        """
    except Exception as e:
        all_price_info += f"\n 1mg search failed: {str(e)}"

    # search pharmeasy price
    try:
        print("   Checking PharmEasy...")
        query_pharmeasy = f"site:pharmeasy.in {medicine} price MRP India rupees"
        result_pharmeasy = search_tool.run(query_pharmeasy)
        all_price_info += f"""
        PharmEasy Price Results:
        {result_pharmeasy[:600]}
        """
    except Exception as e:
        all_price_info += f"\n PharmEasy search failed: {str(e)}"

    # search netmeds price
    try:
        print("   Checking Netmeds...")
        query_netmeds = f"site:netmeds.com {medicine} price MRP India rupees"
        result_netmeds = search_tool.run(query_netmeds)
        all_price_info += f"""
        Netmeds Price Results:
        {result_netmeds[:600]}
        """
    except Exception as e:
        all_price_info += f"\n Netmeds search failed: {str(e)}"

    # search generic medicine price in india
    try:
        print("   Checking generic price in India...")
        query_generic = f"{medicine} generic medicine price India rupees Jan Aushadhi"
        result_generic = search_tool.run(query_generic)
        all_price_info += f"""
        Generic Medicine Price in India:
        {result_generic[:600]}
        """
    except Exception as e:
        all_price_info += f"\n Generic price search failed: {str(e)}"

    # search nppa controlled price
    try:
        print("   Checking NPPA government price...")
        query_nppa = f"NPPA price list {medicine} India government controlled price rupees"
        result_nppa = search_tool.run(query_nppa)
        all_price_info += f"""
        NPPA Government Price Info:
        {result_nppa[:600]}
        """
    except Exception as e:
        all_price_info += f"\n NPPA search failed: {str(e)}"

    # add a note about jan aushadhi stores
    all_price_info += """
    
    Note about Jan Aushadhi:
    Jan Aushadhi stores are government stores in India
    that sell generic medicines at very low prices.
    Prices there can be 50-90% cheaper than brand medicines.
    Website: janaushadhi.gov.in
    """

    return {"indian_price_data": all_price_info}


# step 5 - search internet for extra info if needed
def search_internet(state: MedicineState):
    medicine = state["medicine_name"]
    fda_data = state["fda_data"]

    if "No FDA data found" in fda_data or "Could not get" in fda_data:
        print(f"\n FDA data missing, searching internet for: {medicine}")
        try:
            query = f"{medicine} medicine India description uses side effects"
            result = search_tool.run(query)
            search_info = result[:2000]
        except Exception as e:
            search_info = f"Internet search failed: {str(e)}"
    else:
        print("\n FDA data found, skipping extra search")
        search_info = "Extra search not needed"

    return {"search_data": search_info}


# step 6 - use ai to create the final output
def generate_final_output(state: MedicineState):
    medicine = state["medicine_name"]
    print(f"\n Generating final report for: {medicine}")

    all_data = f"""
    Medicine Name: {medicine}

    FDA Data:
    {state['fda_data']}

    RxNorm Alternatives:
    {state['rxnorm_data']}

    Composition Data:
    {state['composition_data']}

    Indian Price Data:
    {state['indian_price_data']}

    Extra Search Data:
    {state['search_data']}
    """

    prompt = f"""
    You are a medical information assistant for Indian users.
    Using the data below, create a clear medicine report with Indian prices in Rupees.

    Data collected:
    {all_data}

    Please create a report with these exact sections:

    1. MEDICINE DESCRIPTION
    Write a simple 3-4 sentence description of {medicine}.

    2. USES AND PURPOSE
    List the main uses in simple bullet points.

    3. COMPOSITION DETAILS
    List the active and inactive ingredients clearly.

    4. COMPOSITION COMPARISON TABLE
    Compare brand vs generic composition.

    | Ingredient        | {medicine} (Brand) | Generic Version     |
    |-------------------|--------------------|---------------------|
    | Active Ingredient | ...                | ...                 |
    | Strength          | ...                | ...                 |
    | Inactive Fillers  | ...                | ...                 |
    | Dosage Form       | ...                | ...                 |

    5. INDIAN PRICE COMPARISON TABLE
    Use prices from the data above. Show prices in Indian Rupees.

    | Price Factor        | {medicine} (Brand) | Generic Version     |
    |---------------------|--------------------|---------------------|
    | Price (1mg.com)     | Rs. ...            | Rs. ...             |
    | Price (PharmEasy)   | Rs. ...            | Rs. ...             |
    | Price (Netmeds)     | Rs. ...            | Rs. ...             |
    | Jan Aushadhi Price  | Rs. ...            | Rs. ...             |
    | Price per Tablet    | Rs. ...            | Rs. ...             |
    | NPPA Ceiling Price  | Rs. ...            | Rs. ...             |
    | Possible Savings    | -                  | Rs. ... (xx% less)  |

    6. WHERE TO BUY IN INDIA
    List the best places to buy this medicine cheaply in India.
    Include Jan Aushadhi stores, online pharmacies, and tips.

    7. ALTERNATIVES LIST
    List 3-5 alternative medicines available in India with:
    - Medicine name
    - Active ingredient
    - Approximate Indian price
    - One line description

    8. IMPORTANT DISCLAIMER
    - Prices are from web search and may vary
    - Check actual pharmacy for final price
    - NPPA controls maximum price for essential medicines
    - Consult a doctor before changing medicines
    - Jan Aushadhi stores have the cheapest generic medicines in India

    Keep everything simple. Use Rupee symbol Rs. for all prices.
    If exact price not found, write "Check pharmacy" instead of guessing.
    """

    response = llm.invoke(prompt)
    final_output = response.content

    return {"final_output": final_output}


# build the langgraph workflow
def build_graph():
    graph = StateGraph(MedicineState)

    graph.add_node("get_fda_info", get_fda_info)
    graph.add_node("get_rxnorm_alternatives", get_rxnorm_alternatives)
    graph.add_node("get_composition", get_composition)
    graph.add_node("get_indian_price", get_indian_price)
    graph.add_node("search_internet", search_internet)
    graph.add_node("generate_final_output", generate_final_output)

    graph.set_entry_point("get_fda_info")
    graph.add_edge("get_fda_info", "get_rxnorm_alternatives")
    graph.add_edge("get_rxnorm_alternatives", "get_composition")
    graph.add_edge("get_composition", "get_indian_price")
    graph.add_edge("get_indian_price", "search_internet")
    graph.add_edge("search_internet", "generate_final_output")
    graph.add_edge("generate_final_output", END)

    return graph.compile()


# main function
def find_medicine_info(medicine_name):
    print(f"\n{'='*60}")
    print(f"  Medicine Comparison Finder - India")
    print(f"{'='*60}")
    print(f"  Looking up: {medicine_name}")

    app = build_graph()

    initial_state = {
        "medicine_name": medicine_name,
        "fda_data": "",
        "rxnorm_data": "",
        "composition_data": "",
        "indian_price_data": "",
        "search_data": "",
        "final_output": ""
    }

    result = app.invoke(initial_state)

    print(f"\n{'='*60}")
    print("  FINAL REPORT")
    print(f"{'='*60}")
    print(result["final_output"])

    return result["final_output"]


# run the program
if __name__ == "__main__":
    print("Medicine Comparison and Alternative Finder - India")
    print("Shows Indian pharmacy prices in Rupees")
    print("-" * 60)

    medicine = input("\nEnter medicine name: ").strip()

    if medicine:
        find_medicine_info(medicine)
    else:
        print("No medicine name entered. Please try again.")