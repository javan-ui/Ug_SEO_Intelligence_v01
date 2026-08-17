"""Exact seed concepts from the Uganda SEO intelligence research plan."""

CORE_SEEDS = """
website design Uganda
website design
web design Uganda
web design
website development Uganda
web development Uganda
website developer Uganda
web developer Uganda
website designer Uganda
web designer Uganda
website design company Uganda
web design company Uganda
website development company Uganda
web development company Uganda
website agency Uganda
web agency Uganda
web development services Uganda
website development services Uganda
website design services Uganda
web design services Uganda
best website designer Uganda
best web designer Uganda
best website design company Uganda
best web development company Uganda
affordable website design Uganda
cheap website design Uganda
professional website design Uganda
professional web design Uganda
custom website design Uganda
custom website development Uganda
website design prices Uganda
website design cost Uganda
how much does a website cost in Uganda
website development cost Uganda
web design prices Uganda
web developer prices Uganda
website company Uganda
website design services Kampala
web design services Kampala
website developer Kampala
web designer Kampala
website for small business Uganda
small business website Uganda
business website Uganda
website for business Uganda
business website design Uganda
business website development Uganda
website for company Uganda
company website Uganda
website for startups Uganda
startup website Uganda
website for local business Uganda
website for entrepreneurs Uganda
online presence for business Uganda
get business online Uganda
take business online Uganda
ecommerce website Uganda
ecommerce website design Uganda
ecommerce website development Uganda
online store Uganda
online shop website Uganda
online store website Uganda
ecommerce developer Uganda
ecommerce web designer Uganda
sell online Uganda website
create online store Uganda
build online store Uganda
online shopping website development Uganda
restaurant website Uganda
hotel website Uganda
school website Uganda
hospital website Uganda
clinic website Uganda
law firm website Uganda
real estate website Uganda
construction company website Uganda
accounting firm website Uganda
consultancy website Uganda
NGO website Uganda
church website Uganda
company website Kampala
restaurant website Kampala
hotel website Kampala
school website Kampala
real estate website Kampala
lawyer website Uganda
SEO Uganda
SEO services Uganda
SEO company Uganda
SEO agency Uganda
local SEO Uganda
Google ranking Uganda
rank on Google Uganda
how to rank on Google Uganda
Google business profile Uganda
Google Business Profile optimization Uganda
Google Maps business Uganda
local business SEO Uganda
SEO services Kampala
SEO company Kampala
Google ranking services Uganda
domain name Uganda
website hosting Uganda
web hosting Uganda
website hosting prices Uganda
domain prices Uganda
website maintenance Uganda
website maintenance services Uganda
WordPress website Uganda
WordPress developer Uganda
WordPress website design Uganda
business email Uganda website
professional email Uganda
how to create a website in Uganda
how to build a website in Uganda
how to make a website in Uganda
cost of building a website in Uganda
cost of website in Uganda
how much is a website in Uganda
how to put a business online Uganda
how to advertise business on Google Uganda
how to get customers from Google Uganda
how to get my business on Google Uganda
how to create a Google business profile Uganda
why business needs a website Uganda
do small businesses need a website Uganda
""".strip().splitlines()

LOCATIONS = [
    "Kampala",
    "Wakiso",
    "Entebbe",
    "Jinja",
    "Mbarara",
    "Mbale",
    "Gulu",
    "Fort Portal",
    "Masaka",
    "Mukono",
]


def seed_records() -> list[dict[str, str]]:
    return [
        {
            "keyword": seed.strip(),
            "source_seed": seed.strip(),
            "discovery_method": "manual_seed",
            "discovery_query": seed.strip(),
        }
        for seed in CORE_SEEDS
        if seed.strip()
    ]