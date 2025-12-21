"""
Test Cases Dataset.

50 enterprise test cases across various industries for testing
the Self-Consistency workflow.
"""

from contexts.testing.models import TestCase

# All 50 test cases from the original n8n workflow
TEST_CASES: list[TestCase] = [
    # --- HIGH COMPLIANCE (10) ---
    TestCase(
        company="Latham & Watkins LLP",
        prompt="Analyze Latham & Watkins at https://www.lw.com and recommend the top 5 AI workflows for automation for automating cross-border M&A due diligence document review, based on real-world results from similar Global Law Firms and white papers.",
        category="High Compliance",
    ),
    TestCase(
        company="Kirkland & Ellis LLP",
        prompt="Analyze Kirkland & Ellis at https://www.kirkland.com and recommend the top 5 AI workflows for automation for identifying conflicts of interest in new client intake, based on real-world results from similar Corporate Law Firms and white papers.",
        category="High Compliance",
    ),
    TestCase(
        company="Mayo Clinic",
        prompt="Analyze Mayo Clinic at https://www.mayoclinic.org and recommend the top 5 AI workflows for automation for triaging international patient referral requests while maintaining HIPAA compliance, based on real-world results from similar Research Hospitals and white papers.",
        category="High Compliance",
    ),
    TestCase(
        company="Cleveland Clinic",
        prompt="Analyze Cleveland Clinic at https://my.clevelandclinic.org and recommend the top 5 AI workflows for automation for summarizing patient histories from disparate EHR systems, based on real-world results from similar Healthcare Providers and white papers.",
        category="High Compliance",
    ),
    TestCase(
        company="JPMorgan Chase",
        prompt="Analyze JPMorgan Chase at https://www.jpmorganchase.com and recommend the top 5 AI workflows for automation for detecting real-time fraud in cross-border wire transfers, based on real-world results from similar Global Investment Banks and white papers.",
        category="High Compliance",
    ),
    TestCase(
        company="Goldman Sachs",
        prompt="Analyze Goldman Sachs at https://www.goldmansachs.com and recommend the top 5 AI workflows for automation for automating regulatory reporting (e.g., MiFID II, Dodd-Frank), based on real-world results from similar Financial Institutions and white papers.",
        category="High Compliance",
    ),
    TestCase(
        company="Pfizer",
        prompt="Analyze Pfizer at https://www.pfizer.com and recommend the top 5 AI workflows for automation for monitoring adverse drug reaction reports from social media and medical literature, based on real-world results from similar Pharmaceutical Companies and white papers.",
        category="High Compliance",
    ),
    TestCase(
        company="Merck",
        prompt="Analyze Merck at https://www.merck.com and recommend the top 5 AI workflows for automation for optimizing clinical trial patient recruitment and retention, based on real-world results from similar BioPharma Companies and white papers.",
        category="High Compliance",
    ),
    TestCase(
        company="Lockheed Martin",
        prompt="Analyze Lockheed Martin at https://www.lockheedmartin.com and recommend the top 5 AI workflows for automation for predictive maintenance of aerospace components using IoT data, based on real-world results from similar Defense Contractors and white papers.",
        category="High Compliance",
    ),
    TestCase(
        company="Boeing",
        prompt="Analyze Boeing at https://www.boeing.com and recommend the top 5 AI workflows for automation for automating supply chain risk assessment for critical aircraft parts, based on real-world results from similar Aerospace Manufacturers and white papers.",
        category="High Compliance",
    ),

    # --- DATA HEAVY (10) ---
    TestCase(
        company="Nielsen",
        prompt="Analyze Nielsen at https://www.nielsen.com and recommend the top 5 AI workflows for automation for aggregating and normalizing viewership data from streaming platforms, based on real-world results from similar Market Research Firms and white papers.",
        category="Data Heavy",
    ),
    TestCase(
        company="Equifax",
        prompt="Analyze Equifax at https://www.equifax.com and recommend the top 5 AI workflows for automation for resolving consumer credit dispute tickets automatically, based on real-world results from similar Credit Bureaus and white papers.",
        category="Data Heavy",
    ),
    TestCase(
        company="Spotify",
        prompt="Analyze Spotify at https://www.spotify.com and recommend the top 5 AI workflows for automation for tagging and categorizing user-generated podcast content, based on real-world results from similar Streaming Platforms and white papers.",
        category="Data Heavy",
    ),
    TestCase(
        company="Netflix",
        prompt="Analyze Netflix at https://www.netflix.com and recommend the top 5 AI workflows for automation for generating localized subtitles and metadata for international content, based on real-world results from similar Media Streaming Services and white papers.",
        category="Data Heavy",
    ),
    TestCase(
        company="Uber",
        prompt="Analyze Uber at https://www.uber.com and recommend the top 5 AI workflows for automation for automating driver identity verification and document approval, based on real-world results from similar Gig Economy Platforms and white papers.",
        category="Data Heavy",
    ),
    TestCase(
        company="Airbnb",
        prompt="Analyze Airbnb at https://www.airbnb.com and recommend the top 5 AI workflows for automation for detecting and flagging fraudulent listings or reviews, based on real-world results from similar Travel Marketplaces and white papers.",
        category="Data Heavy",
    ),
    TestCase(
        company="Zillow",
        prompt="Analyze Zillow at https://www.zillow.com and recommend the top 5 AI workflows for automation for estimating property renovation costs from listing photos, based on real-world results from similar Real Estate Tech Companies and white papers.",
        category="Data Heavy",
    ),
    TestCase(
        company="Redfin",
        prompt="Analyze Redfin at https://www.redfin.com and recommend the top 5 AI workflows for automation for scheduling and coordinating home tours with agents, based on real-world results from similar Real Estate Brokerages and white papers.",
        category="Data Heavy",
    ),
    TestCase(
        company="Wayfair",
        prompt="Analyze Wayfair at https://www.wayfair.com and recommend the top 5 AI workflows for automation for visual search and product recommendation based on user-uploaded room photos, based on real-world results from similar E-commerce Furniture Retailers and white papers.",
        category="Data Heavy",
    ),
    TestCase(
        company="Etsy",
        prompt="Analyze Etsy at https://www.etsy.com and recommend the top 5 AI workflows for automation for detecting intellectual property infringement in handmade goods listings, based on real-world results from similar Peer-to-Peer Marketplaces and white papers.",
        category="Data Heavy",
    ),

    # --- CREATIVE / UNSTRUCTURED (10) ---
    TestCase(
        company="Wieden+Kennedy",
        prompt="Analyze Wieden+Kennedy at https://www.wk.com and recommend the top 5 AI workflows for automation for generating storyboard concepts from client briefs, based on real-world results from similar Creative Agencies and white papers.",
        category="Creative",
    ),
    TestCase(
        company="Ogilvy",
        prompt="Analyze Ogilvy at https://www.ogilvy.com and recommend the top 5 AI workflows for automation for analyzing sentiment and trends in social media conversations for brand reputation management, based on real-world results from similar PR & Advertising Firms and white papers.",
        category="Creative",
    ),
    TestCase(
        company="Penguin Random House",
        prompt="Analyze Penguin Random House at https://www.penguinrandomhouse.com and recommend the top 5 AI workflows for automation for analyzing manuscript drafts for marketability and genre fit, based on real-world results from similar Publishing Houses and white papers.",
        category="Creative",
    ),
    TestCase(
        company="BuzzFeed",
        prompt="Analyze BuzzFeed at https://www.buzzfeed.com and recommend the top 5 AI workflows for automation for generating quiz content and headlines based on trending topics, based on real-world results from similar Digital Media Publishers and white papers.",
        category="Creative",
    ),
    TestCase(
        company="MasterClass",
        prompt="Analyze MasterClass at https://www.masterclass.com and recommend the top 5 AI workflows for automation for personalized course curriculum generation based on user goals, based on real-world results from similar EdTech Platforms and white papers.",
        category="Creative",
    ),
    TestCase(
        company="Duolingo",
        prompt="Analyze Duolingo at https://www.duolingo.com and recommend the top 5 AI workflows for automation for generating localized language learning exercises from news articles, based on real-world results from similar Language Learning Apps and white papers.",
        category="Creative",
    ),
    TestCase(
        company="Canva",
        prompt="Analyze Canva at https://www.canva.com and recommend the top 5 AI workflows for automation for suggesting design templates based on user text descriptions, based on real-world results from similar Graphic Design Platforms and white papers.",
        category="Creative",
    ),
    TestCase(
        company="Adobe",
        prompt="Analyze Adobe at https://www.adobe.com and recommend the top 5 AI workflows for automation for automating image tagging and keywording for stock photography, based on real-world results from similar Creative Software Companies and white papers.",
        category="Creative",
    ),
    TestCase(
        company="Unity",
        prompt="Analyze Unity at https://unity.com and recommend the top 5 AI workflows for automation for generating 3D assets from 2D reference images, based on real-world results from similar Game Development Platforms and white papers.",
        category="Creative",
    ),
    TestCase(
        company="Roblox",
        prompt="Analyze Roblox at https://www.roblox.com and recommend the top 5 AI workflows for automation for moderating in-game voice chat in real-time, based on real-world results from similar Gaming Metaverse Platforms and white papers.",
        category="Creative",
    ),

    # --- TECHNICAL / INDUSTRIAL (10) ---
    TestCase(
        company="Schlumberger",
        prompt="Analyze Schlumberger at https://www.slb.com and recommend the top 5 AI workflows for automation for analyzing seismic data to predict drilling risks, based on real-world results from similar Oilfield Services Companies and white papers.",
        category="Technical",
    ),
    TestCase(
        company="Siemens",
        prompt="Analyze Siemens at https://www.siemens.com and recommend the top 5 AI workflows for automation for optimizing energy consumption in smart buildings, based on real-world results from similar Industrial Manufacturing Companies and white papers.",
        category="Technical",
    ),
    TestCase(
        company="General Electric",
        prompt="Analyze General Electric at https://www.ge.com and recommend the top 5 AI workflows for automation for predicting failure in wind turbine components, based on real-world results from similar Power Generation Companies and white papers.",
        category="Technical",
    ),
    TestCase(
        company="Caterpillar",
        prompt="Analyze Caterpillar at https://www.caterpillar.com and recommend the top 5 AI workflows for automation for optimizing parts inventory across global dealerships, based on real-world results from similar Heavy Machinery Manufacturers and white papers.",
        category="Technical",
    ),
    TestCase(
        company="John Deere",
        prompt="Analyze John Deere at https://www.deere.com and recommend the top 5 AI workflows for automation for analyzing satellite imagery to provide crop health recommendations, based on real-world results from similar Agricultural Equipment Manufacturers and white papers.",
        category="Technical",
    ),
    TestCase(
        company="Tesla",
        prompt="Analyze Tesla at https://www.tesla.com and recommend the top 5 AI workflows for automation for analyzing fleet telemetry to improve autopilot software, based on real-world results from similar EV Manufacturers and white papers.",
        category="Technical",
    ),
    TestCase(
        company="SpaceX",
        prompt="Analyze SpaceX at https://www.spacex.com and recommend the top 5 AI workflows for automation for automating pre-launch system checks and anomaly detection, based on real-world results from similar Aerospace Companies and white papers.",
        category="Technical",
    ),
    TestCase(
        company="Maersk",
        prompt="Analyze Maersk at https://www.maersk.com and recommend the top 5 AI workflows for automation for optimizing container shipping routes based on weather and port congestion, based on real-world results from similar Global Logistics Companies and white papers.",
        category="Technical",
    ),
    TestCase(
        company="FedEx",
        prompt="Analyze FedEx at https://www.fedex.com and recommend the top 5 AI workflows for automation for predicting package delivery delays and notifying customers proactively, based on real-world results from similar Logistics & Delivery Services and white papers.",
        category="Technical",
    ),
    TestCase(
        company="Honeywell",
        prompt="Analyze Honeywell at https://www.honeywell.com and recommend the top 5 AI workflows for automation for automating quality control inspection on assembly lines using computer vision, based on real-world results from similar Industrial Technology Companies and white papers.",
        category="Technical",
    ),

    # --- SERVICE / RETAIL (10) ---
    TestCase(
        company="Starbucks",
        prompt="Analyze Starbucks at https://www.starbucks.com and recommend the top 5 AI workflows for automation for personalizing mobile app offers based on purchase history and weather, based on real-world results from similar Global Coffee Chains and white papers.",
        category="Service/Retail",
    ),
    TestCase(
        company="McDonald's",
        prompt="Analyze McDonald's at https://www.mcdonalds.com and recommend the top 5 AI workflows for automation for optimizing drive-thru menu boards based on traffic and time of day, based on real-world results from similar Fast Food Chains and white papers.",
        category="Service/Retail",
    ),
    TestCase(
        company="Marriott International",
        prompt="Analyze Marriott at https://www.marriott.com and recommend the top 5 AI workflows for automation for automating concierge requests for dining and activity reservations, based on real-world results from similar Hotel Chains and white papers.",
        category="Service/Retail",
    ),
    TestCase(
        company="Hilton",
        prompt="Analyze Hilton at https://www.hilton.com and recommend the top 5 AI workflows for automation for predicting room maintenance needs before guest arrival, based on real-world results from similar Hospitality Companies and white papers.",
        category="Service/Retail",
    ),
    TestCase(
        company="Delta Air Lines",
        prompt="Analyze Delta at https://www.delta.com and recommend the top 5 AI workflows for automation for rebooking passengers automatically during weather disruptions, based on real-world results from similar Commercial Airlines and white papers.",
        category="Service/Retail",
    ),
    TestCase(
        company="American Express",
        prompt="Analyze American Express at https://www.americanexpress.com and recommend the top 5 AI workflows for automation for analyzing spending patterns to offer personalized travel concierge services, based on real-world results from similar Financial Services Companies and white papers.",
        category="Service/Retail",
    ),
    TestCase(
        company="Walmart",
        prompt="Analyze Walmart at https://www.walmart.com and recommend the top 5 AI workflows for automation for optimizing shelf restocking schedules using sales velocity data, based on real-world results from similar Big Box Retailers and white papers.",
        category="Service/Retail",
    ),
    TestCase(
        company="Target",
        prompt="Analyze Target at https://www.target.com and recommend the top 5 AI workflows for automation for predicting fashion trends to inform inventory buying, based on real-world results from similar Retail Chains and white papers.",
        category="Service/Retail",
    ),
    TestCase(
        company="Home Depot",
        prompt="Analyze Home Depot at https://www.homedepot.com and recommend the top 5 AI workflows for automation for identifying DIY project upsell opportunities based on cart contents, based on real-world results from similar Home Improvement Retailers and white papers.",
        category="Service/Retail",
    ),
    TestCase(
        company="CVS Health",
        prompt="Analyze CVS Health at https://www.cvs.com and recommend the top 5 AI workflows for automation for reminding patients to refill prescriptions based on usage patterns, based on real-world results from similar Pharmacy & Healthcare Companies and white papers.",
        category="Service/Retail",
    ),
]


def get_test_cases(count: int = 50) -> list[TestCase]:
    """
    Get test cases, limited by count.

    Args:
        count: Number of test cases to return (1-50)

    Returns:
        List of TestCase objects
    """
    count = max(1, min(count, len(TEST_CASES)))
    return TEST_CASES[:count]


def get_test_cases_by_category(category: str) -> list[TestCase]:
    """
    Get test cases filtered by category.

    Args:
        category: Category name (e.g., "High Compliance", "Creative")

    Returns:
        List of TestCase objects in that category
    """
    return [tc for tc in TEST_CASES if tc.category == category]
