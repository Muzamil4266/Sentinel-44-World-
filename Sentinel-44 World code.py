# ============================================================
# SENTINEL GLOBAL DATA COLLECTOR — 44 ELEMENTS
# STRICT: Current calendar month data ONLY
# No paid APIs. All sources are free.
# ============================================================

import requests
import json
import numpy as np
import feedparser
import time
import warnings
import calendar
from datetime import datetime, timedelta
from textblob import TextBlob

warnings.filterwarnings('ignore')

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    print("⚠️  yfinance not installed — run: pip install yfinance")

# ── Optional free API keys ─────────────────────────────────────────────────────
# FRED: https://fred.stlouisfed.org/docs/api/api_key.html
FRED_API_KEY = "YOUR_FRED_API_KEY"
# EIA:  https://www.eia.gov/opendata/register.php
EIA_API_KEY  = "YOUR_EIA_API_KEY"
# ──────────────────────────────────────────────────────────────────────────────


class Sentinel44Collector:

    def __init__(self):
        self.now          = datetime.utcnow()
        self.timestamp    = self.now.isoformat() + "Z"
        self.month_start  = self.now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        self.alerts   = []
        self.patterns = []
        self.news_headlines_count = 0
        self.avg_sentiment        = 0.0
        self.keyword_counts       = {}

        self._init_elements()
        self._init_keywords()

    # ──────────────────────────────────────────────────────────────────────────
    # ELEMENT DEFINITIONS
    # ──────────────────────────────────────────────────────────────────────────
    def _init_elements(self):
        b = lambda extra={}: {"score": 0.0, "indicators": [], "mentions": 0, **extra}
        self.elements = {
            # ── ORIGINAL 31 ──────────────────────────────────────────────────
            "1_war_conflict":           b(),
            "2_inflation":              b({"countries": []}),
            "3_tariffs_trade":          b(),
            "4_military_alliances":     b(),
            "5_elections":              b(),
            "6_science_tech":           b(),
            "7_protests_unrest":        b(),
            "8_immigration":            b(),
            "9_visa_policies":          b(),
            "10_sanctions":             b(),
            "11_energy_crisis":         b({"price_data": {}}),
            "12_food_security":         b(),
            "13_debt_crisis":           b({"countries": []}),
            "14_cyber_warfare":         b(),
            "15_climate_disasters":     b({"events": []}),
            "16_disease_outbreaks":     b({"alerts": []}),
            "17_nuclear":               b(),
            "18_space_race":            b(),
            "19_diplomacy":             b(),
            "20_terrorism":             b(),
            "21_trade_agreements":      b(),
            "22_interest_rates":        b({"central_banks": []}),
            "23_commodity_prices":      b({"commodities": {}}),
            "24_supply_chains":         b(),
            "25_labor_strikes":         b({"labor_data": {}}),
            "26_housing_crisis":        b(),
            "27_tech_monopolies":       b(),
            "28_demographics":          b(),
            "29_religious_tensions":    b(),
            "30_corporate_takeovers":   b(),
            "31_stock_market":          b({"indices": {}, "sector_performance": {},
                                           "volatility": 0.0, "trend": "neutral"}),
            # ── NEW 13 ───────────────────────────────────────────────────────
            "32_india":                 b({"sub_topics": []}),
            "33_usa":                   b({"sub_topics": []}),
            "34_china":                 b({"sub_topics": []}),
            "35_russia":                b({"sub_topics": []}),
            "36_middle_east":           b({"sub_topics": []}),
            "37_africa":                b({"sub_topics": []}),
            "38_semiconductor_war":     b({"sub_topics": []}),
            "39_ai_race":               b({"sub_topics": []}),
            "40_critical_minerals":     b({"sub_topics": []}),
            "41_disinformation":        b({"sub_topics": []}),
            "42_water_wars":            b({"sub_topics": []}),
            "43_cryptocurrency":        b({"coins": {}, "sub_topics": []}),
            "44_grid_infrastructure":   b({"sub_topics": []}),
        }

    # ──────────────────────────────────────────────────────────────────────────
    # KEYWORDS
    # ──────────────────────────────────────────────────────────────────────────
    def _init_keywords(self):
        self.keyword_counts = {k: 0 for k in [
            # original
            'war','conflict','inflation','tariff','trade','military','election',
            'protest','sanction','oil','gas','energy','food','debt','cyber',
            'climate','disease','nuclear','space','stock','market','nasdaq',
            'vix','visa','immigration','housing','labor','religion','merger',
            'earthquake','flood','wildfire','hurricane','terror','hack',
            # new
            'india','modi','delhi','rupee','pakistan','border','lac',
            'usa','trump','biden','fed','dollar','pentagon','congress',
            'china','xi','beijing','taiwan','pla','huawei','yuan',
            'russia','putin','kremlin','ukraine','wagner','arctic',
            'iran','israel','saudi','houthi','gaza','hezbollah',
            'africa','sahel','coup','mineral','cobalt','lithium',
            'semiconductor','chip','tsmc','nvidia','export control',
            'artificial intelligence','llm','openai','deepseek','gemini',
            'rare earth','copper','manganese','graphite',
            'disinformation','deepfake','propaganda','psyop','influence operation',
            'water','dam','river','drought','aquifer','nile','mekong',
            'bitcoin','crypto','ethereum','stablecoin','cbdc','defi',
            'power grid','pipeline','sabotage','infrastructure attack','blackout',
        ]}

    # ──────────────────────────────────────────────────────────────────────────
    # HELPER: ASYMPTOTIC SCORING (Prevents hitting 100 immediately)
    # ──────────────────────────────────────────────────────────────────────────
    def _add_score(self, element, add_val):
        """Adds a percentage of the remaining distance to 100."""
        curr = self.elements[element]["score"]
        self.elements[element]["score"] = curr + (100.0 - curr) * (add_val / 100.0)

    # ──────────────────────────────────────────────────────────────────────────
    # HELPER: current-month date gate for RSS entries
    # ──────────────────────────────────────────────────────────────────────────
    def _is_current_month(self, entry) -> bool:
        pub = entry.get("published_parsed") or entry.get("updated_parsed")
        if pub is None:
            return True
        try:
            pub_dt = datetime.utcfromtimestamp(calendar.timegm(pub))
            return pub_dt >= self.month_start
        except Exception:
            return True

    # ──────────────────────────────────────────────────────────────────────────
    # HELPER: fetch + filter a single RSS feed
    # ──────────────────────────────────────────────────────────────────────────
    def _rss_headlines(self, url: str, max_entries: int = 40) -> list:
        headlines = []
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:max_entries]:
                if not self._is_current_month(entry):
                    continue
                text = (entry.get('title', '') + " " + entry.get('summary', '')).strip()
                if text:
                    headlines.append(text)
        except Exception as ex:
            print(f"   ⚠️  RSS failed: {url[:70]} → {ex}")
        return headlines

    # ──────────────────────────────────────────────────────────────────────────
    # CATEGORIZATION — maps text → element scores (original 31)
    # ──────────────────────────────────────────────────────────────────────────
    def _categorize(self, text: str, sentiment: float = 0.0):
        tl = text.lower()
        cat_map = [
            (['war','conflict','battle','shelling','airstrike','troops','offensive'],       "1_war_conflict"),
            (['inflation','cpi','consumer price','cost of living','price surge'],           "2_inflation"),
            (['tariff','trade war','import duty','export ban','trade restriction'],         "3_tariffs_trade"),
            (['nato','alliance','military pact','defense agreement','joint exercise'],      "4_military_alliances"),
            (['election','ballot','vote','polling','referendum','candidate'],               "5_elections"),
            (['artificial intelligence','ai chip','tech breakthrough','research','chip'],   "6_science_tech"),
            (['protest','riot','demonstration','uprising','unrest','rally'],                "7_protests_unrest"),
            (['immigration','migrant','refugee','asylum','border crossing','deportation'],  "8_immigration"),
            (['visa','travel ban','border control','entry restriction'],                    "9_visa_policies"),
            (['sanction','embargo','asset freeze','blacklist','export control'],            "10_sanctions"),
            (['oil','gas','energy','power outage','fuel','electricity shortage'],           "11_energy_crisis"),
            (['food','wheat','grain','hunger','famine','food price','crop'],                "12_food_security"),
            (['debt','default','imf','bailout','credit rating','bond yield'],              "13_debt_crisis"),
            (['cyber','hack','breach','ransomware','ddos','data leak','phishing'],         "14_cyber_warfare"),
            (['flood','drought','wildfire','cyclone','hurricane','typhoon','earthquake'],  "15_climate_disasters"),
            (['disease','outbreak','pandemic','virus','epidemic','mpox','cholera'],        "16_disease_outbreaks"),
            (['nuclear','uranium','atomic','nuke','warhead','icbm'],                       "17_nuclear"),
            (['space','rocket','launch','satellite','moon','mars','orbit','nasa','spacex'],"18_space_race"),
            (['diplomacy','summit','ceasefire','peace talks','negotiation','envoy'],       "19_diplomacy"),
            (['terror','attack','bomb','explosion','militia','armed group'],               "20_terrorism"),
            (['trade deal','trade agreement','partnership','treaty','pact signed'],        "21_trade_agreements"),
            (['interest rate','federal reserve','fed rate','central bank','rate hike',
              'rate cut','boe','ecb','rbi rate'],                                          "22_interest_rates"),
            (['gold','copper','lithium','silver','commodity','iron ore'],                  "23_commodity_prices"),
            (['supply chain','logistics','shipping','container','port congestion'],        "24_supply_chains"),
            (['strike','labor','union','worker','walkout','picket','wage'],                "25_labor_strikes"),
            (['housing','real estate','mortgage','rent','property market'],                "26_housing_crisis"),
            (['antitrust','monopoly','big tech','regulation','breakup','fine'],            "27_tech_monopolies"),
            (['population','birth rate','aging','demographic','migration trend'],          "28_demographics"),
            (['religious','sectarian','church','mosque','temple','faith','jihad'],         "29_religious_tensions"),
            (['acquisition','merger','takeover','buyout','m&a','deal signed'],            "30_corporate_takeovers"),
            (['stock market','s&p','dow jones','nasdaq','market crash','vix',
              'bull market','bear market','selloff','rally','equities'],                   "31_stock_market"),
        ]
        for keywords, element in cat_map:
            if any(w in tl for w in keywords):
                self.elements[element]["indicators"].append(text[:120])
                self.elements[element]["mentions"] += 1
                self._add_score(element, 5)

        # ── keyword counter ──
        for kw in self.keyword_counts:
            if kw in tl:
                self.keyword_counts[kw] += 1

    # ──────────────────────────────────────────────────────────────────────────
    # NEW ELEMENT CATEGORIZATION (32–44)
    # ──────────────────────────────────────────────────────────────────────────
    def _categorize_new(self, text: str):
        tl = text.lower()

        new_map = [
            # 32 India — international angles: border, trade, energy, diaspora, RBI
            (["india","modi","new delhi","rupee","rbi","indian army","lac","line of control",
              "india pakistan","india china","quad india","brics india","india trade",
              "india sanctions","india oil","india russia","india export","india import",
              "india us","india diplomacy","india missile","india border","indian rupee",
              "indian economy","india inflation","india gdp"],
             "32_india"),

            # 33 USA — fed, congress, military, dollar, debt ceiling, executive orders
            (["united states","u.s.","us government","trump","white house","pentagon",
              "congress","senate","federal reserve","us fed","dollar index","dxy",
              "us military","us tariff","us sanction","us election","us debt",
              "us treasury","us tech","us chip","us ai","us export control",
              "us nato","us china","us russia","us india","us iran","us israel",
              "us economy","us inflation","us jobs","us gdp","us president"],
             "33_usa"),

            # 34 China — taiwan, pla, belt road, yuan, evergrande, chip ban
            (["china","xi jinping","beijing","pla","peoples liberation army","taiwan strait",
              "taiwan independence","south china sea","belt and road","bri","yuan","renminbi",
              "huawei","tiktok","china chip","china semiconductor","china sanctions",
              "china russia","china india","china africa","china economy","china property",
              "evergrande","china inflation","china gdp","china military","china navy",
              "china rare earth","china export","china trade","china us","china eu"],
             "34_china"),

            # 35 Russia — ukraine, energy leverage, arctic, wagner, nuclear
            (["russia","putin","kremlin","moscow","ukraine","russian army","russian military",
              "russian oil","russian gas","nord stream","russian sanction","ruble",
              "wagner","prigozhin","russian arctic","russian nuclear","russian missile",
              "russian navy","russia nato","russia china","russia iran","russia india",
              "russian economy","russian default","russian propaganda","russia africa"],
             "35_russia"),

            # 36 Middle East — iran, israel, saudi, houthi, red sea, oil
            (["middle east","iran","israel","saudi arabia","houthi","red sea","gaza",
              "west bank","hezbollah","hamas","iran nuclear","iran sanctions",
              "opec","aramco","persian gulf","strait of hormuz","lebanese","syria",
              "iraq","yemen","uae","qatar","bahrain","jordan","egypt","suez",
              "iran us","iran israel","saudi us","middle east war","arab","gulf"],
             "36_middle_east"),

            # 37 Africa — coups, china influence, minerals, sahel, food
            (["africa","sahel","niger","mali","burkina faso","sudan","ethiopia",
              "somalia","congo","drc","kenya","nigeria","south africa","ghana",
              "african coup","african military","african election","china africa",
              "africa mineral","africa cobalt","africa lithium","africa oil",
              "africa food","africa famine","africa drought","africa debt",
              "africa us","africa eu","africa russia","ecowas","african union"],
             "37_africa"),

            # 38 Semiconductor War — chips, tsmc, nvidia, export controls
            (["semiconductor","chip war","tsmc","nvidia","intel","amd","asml",
              "chip ban","chip export","chip sanction","chip factory","fab",
              "advanced chip","chip shortage","chip supply","chip act",
              "chip technology","chip restriction","chip production","3nm","2nm",
              "chip us china","chip taiwan","chip embargo","chip control",
              "chipmaker","wafer","chip design","arm holdings","chip stock"],
             "38_semiconductor_war"),

            # 39 AI Race — llm, regulation, us china ai, openai, deepseek
            (["artificial intelligence","ai race","ai regulation","ai governance",
              "openai","deepseek","gemini","grok","llama","claude ai","gpt",
              "large language model","llm","ai chip","ai compute","ai ban",
              "ai safety","ai act","ai policy","ai military","ai weapon",
              "ai surveillance","ai china","ai us","ai europe","ai regulation",
              "ai investment","ai startup","ai model","ai benchmark","ai power"],
             "39_ai_race"),

            # 40 Critical Minerals — lithium, cobalt, rare earth, graphite, manganese
            (["critical mineral","rare earth","lithium","cobalt","graphite","manganese",
              "nickel","tungsten","gallium","germanium","indium","neodymium",
              "mineral supply","mineral mine","mineral export","mineral ban",
              "mineral china","mineral africa","mineral congo","mineral australia",
              "mineral us","ev battery","battery mineral","mineral war","mining rights",
              "mineral sanction","mineral control","mineral trade","mineral reserve"],
             "40_critical_minerals"),

            # 41 Disinformation — deepfake, propaganda, election interference, psyop
            (["disinformation","misinformation","deepfake","propaganda","fake news",
              "influence operation","psyop","information warfare","state media",
              "bot network","troll farm","election interference","social media manipulation",
              "russian propaganda","chinese propaganda","information war","narrative control",
              "fake account","coordinated inauthentic","media manipulation","censorship",
              "internet shutdown","press freedom","journalist arrested","media ban"],
             "41_disinformation"),

            # 42 Water Wars — nile dam, mekong, aquifer, water conflict, drought
            (["water war","water conflict","water crisis","water scarcity","dam dispute",
              "nile dam","grand ethiopian renaissance dam","gerd","mekong river",
              "water rights","transboundary water","aquifer","water table","water stress",
              "river dispute","water sharing","india water","pakistan water","indus waters",
              "water treaty","water shortage","water security","water diplomacy",
              "groundwater","desalination","water privatization","drought conflict"],
             "42_water_wars"),

            # 43 Crypto — bitcoin, ethereum, stablecoin, cbdc, defi, regulation
            (["bitcoin","ethereum","crypto","cryptocurrency","stablecoin","tether","usdc",
              "cbdc","digital currency","defi","nft","blockchain","crypto regulation",
              "crypto ban","crypto exchange","binance","coinbase","crypto crash",
              "crypto rally","crypto sanction","crypto hack","crypto fraud",
              "crypto market","btc","eth","altcoin","crypto us","crypto china",
              "crypto india","crypto law","crypto tax","digital asset"],
             "43_cryptocurrency"),

       
            # 44 Grid & Infrastructure Attacks — power grid, pipeline, sabotage
            (["power grid","grid attack","grid outage","blackout","infrastructure attack",
              "pipeline attack","pipeline sabotage","undersea cable","cable cut",
              "nord stream","power plant attack","dam attack","water supply attack",
              "critical infrastructure","grid hack","grid vulnerability","substation",
              "power disruption","energy infrastructure","grid resilience","grid failure",
              "internet cable","fiber cut","satellite attack","gps jamming",
              "infrastructure sabotage","bridge attack","port attack","rail attack"],
             "44_grid_infrastructure"),
        ]

        for keywords, element in new_map:
            if any(w in tl for w in keywords):
                self.elements[element]["mentions"] += 1
                self._add_score(element, 5)
                snippet = text[:120]
                if snippet not in self.elements[element]["indicators"]:
                    self.elements[element]["indicators"].append(snippet)
                if snippet not in self.elements[element]["sub_topics"]:
                    self.elements[element]["sub_topics"].append(snippet)

    # ──────────────────────────────────────────────────────────────────────────
    # 1. GLOBAL NEWS RSS — original broad feeds
    # ──────────────────────────────────────────────────────────────────────────
    def fetch_news_data(self):
        print("📰 [NEWS] Fetching global RSS feeds — current month only...")
        feeds = [
            # broad world news
            "http://feeds.bbci.co.uk/news/world/rss.xml",
            "http://rss.cnn.com/rss/edition_world.rss",
            "https://www.aljazeera.com/xml/rss/all.xml",
            "https://feeds.reuters.com/reuters/worldNews",
            "https://feeds.reuters.com/reuters/businessNews",
            # google news topic feeds
            "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFZ4ZDJZS0VnWmxkV1FzQUFQAQ?hl=en-US&gl=US&ceid=US:en",
            # google news search feeds — broad topics
            "https://news.google.com/rss/search?q=war+conflict+sanctions&hl=en-US&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q=inflation+economy+central+bank&hl=en-US&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q=election+protest+strike&hl=en-US&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q=cyber+attack+hack+breach&hl=en-US&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q=nuclear+missile+weapon&hl=en-US&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q=disease+outbreak+virus+epidemic&hl=en-US&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q=oil+gas+energy+price&hl=en-US&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q=food+wheat+grain+famine&hl=en-US&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q=tariff+trade+sanction+embargo&hl=en-US&gl=US&ceid=US:en",
        ]
        all_headlines = []
        skipped = 0
        for url in feeds:
            hl = self._rss_headlines(url, 40)
            for text in hl:
                all_headlines.append(text)
                self._categorize(text, TextBlob(text).sentiment.polarity)
                self._categorize_new(text)
            skipped_feed = len(feedparser.parse(url).entries[:40]) - len(hl)
            skipped += max(skipped_feed, 0)

        self.news_headlines_count = len(all_headlines)
        sents = [TextBlob(h).sentiment.polarity for h in all_headlines[:300]]
        self.avg_sentiment = round(float(np.mean(sents)), 3) if sents else 0.0
        print(f"   → {len(all_headlines)} current-month headlines | ~{skipped} old skipped")


    # ──────────────────────────────────────────────────────────────────────────
    # 2. COUNTRY & TOPIC SPECIFIC RSS FEEDS (new elements 32–44)
    # ──────────────────────────────────────────────────────────────────────────
    def fetch_country_topic_feeds(self):
        print("🌐 [COUNTRY/TOPIC RSS] Fetching targeted feeds — current month only...")

        topic_feeds = {
            "32_india": [
                "https://feeds.feedburner.com/ndtvnews-india-news",
                "https://www.thehindu.com/news/international/feeder/default.rss",
                "https://news.google.com/rss/search?q=India+international+border+trade+diplomacy&hl=en-IN&gl=IN&ceid=IN:en",
                "https://news.google.com/rss/search?q=India+China+LAC+border+2025&hl=en-US&gl=US&ceid=US:en",
                "https://news.google.com/rss/search?q=India+Pakistan+tension+2025&hl=en-US&gl=US&ceid=US:en",
                "https://news.google.com/rss/search?q=India+sanctions+Russia+oil+trade&hl=en-US&gl=US&ceid=US:en",
                "https://news.google.com/rss/search?q=Rupee+RBI+India+economy+global&hl=en-US&gl=US&ceid=US:en",
            ],
            "33_usa": [
                "https://feeds.reuters.com/Reuters/PoliticsNews",
                "https://rss.politico.com/politics-news.xml",
                "https://news.google.com/rss/search?q=USA+Federal+Reserve+interest+rate+2025&hl=en-US&gl=US&ceid=US:en",
                "https://news.google.com/rss/search?q=US+military+deployment+Pentagon+2025&hl=en-US&gl=US&ceid=US:en",
                "https://news.google.com/rss/search?q=US+Congress+Senate+bill+executive+order+2025&hl=en-US&gl=US&ceid=US:en",
                "https://news.google.com/rss/search?q=US+China+trade+war+tariff+2025&hl=en-US&gl=US&ceid=US:en",
                "https://news.google.com/rss/search?q=US+dollar+index+DXY+treasury+2025&hl=en-US&gl=US&ceid=US:en",
                "https://news.google.com/rss/search?q=Trump+White+House+policy+2025&hl=en-US&gl=US&ceid=US:en",
            ],
            "34_china": [
                "https://www.scmp.com/rss/91/feed",
                "https://news.google.com/rss/search?q=China+Taiwan+PLA+military+2025&hl=en-US&gl=US&ceid=US:en",
                "https://news.google.com/rss/search?q=China+South+China+Sea+navy+2025&hl=en-US&gl=US&ceid=US:en",
                "https://news.google.com/rss/search?q=China+economy+yuan+property+2025&hl=en-US&gl=US&ceid=US:en",
                "https://news.google.com/rss/search?q=China+sanctions+export+rare+earth+2025&hl=en-US&gl=US&ceid=US:en",
                "https://news.google.com/rss/search?q=Belt+Road+Initiative+China+2025&hl=en-US&gl=US&ceid=US:en",
                "https://news.google.com/rss/search?q=Xi+Jinping+Beijing+policy+2025&hl=en-US&gl=US&ceid=US:en",
            ],
            "35_russia": [
                "https://feeds.reuters.com/reuters/worldNews",
                "https://news.google.com/rss/search?q=Russia+Ukraine+war+2025&hl=en-US&gl=US&ceid=US:en",
                "https://news.google.com/rss/search?q=Russia+Putin+Kremlin+military+2025&hl=en-US&gl=US&ceid=US:en",
                "https://news.google.com/rss/search?q=Russia+sanctions+oil+gas+2025&hl=en-US&gl=US&ceid=US:en",
                "https://news.google.com/rss/search?q=Russia+nuclear+missile+2025&hl=en-US&gl=US&ceid=US:en",
                "https://news.google.com/rss/search?q=Russia+Arctic+navy+2025&hl=en-US&gl=US&ceid=US:en",
                "https://news.google.com/rss/search?q=Russia+Africa+Wagner+2025&hl=en-US&gl=US&ceid=US:en",
            ],
            "36_middle_east": [
                "https://www.aljazeera.com/xml/rss/all.xml",
                "https://news.google.com/rss/search?q=Iran+nuclear+sanctions+2025&hl=en-US&gl=US&ceid=US:en",
                "https://news.google.com/rss/search?q=Israel+Gaza+West+Bank+2025&hl=en-US&gl=US&ceid=US:en",
                "https://news.google.com/rss/search?q=Houthi+Red+Sea+shipping+2025&hl=en-US&gl=US&ceid=US:en",
                "https://news.google.com/rss/search?q=Saudi+Arabia+OPEC+oil+2025&hl=en-US&gl=US&ceid=US:en",
                "https://news.google.com/rss/search?q=Strait+Hormuz+Persian+Gulf+2025&hl=en-US&gl=US&ceid=US:en",
                "https://news.google.com/rss/search?q=Middle+East+war+ceasefire+2025&hl=en-US&gl=US&ceid=US:en",
            ],
            "37_africa": [
                "https://news.google.com/rss/search?q=Africa+coup+military+2025&hl=en-US&gl=US&ceid=US:en",
                "https://news.google.com/rss/search?q=Sahel+Niger+Mali+Burkina+Faso+2025&hl=en-US&gl=US&ceid=US:en",
                "https://news.google.com/rss/search?q=Africa+China+minerals+investment+2025&hl=en-US&gl=US&ceid=US:en",
                "https://news.google.com/rss/search?q=Africa+food+crisis+famine+2025&hl=en-US&gl=US&ceid=US:en",
                "https://news.google.com/rss/search?q=DRC+Congo+Sudan+Ethiopia+conflict+2025&hl=en-US&gl=US&ceid=US:en",
                "https://news.google.com/rss/search?q=Africa+debt+IMF+default+2025&hl=en-US&gl=US&ceid=US:en",
            ],
            "38_semiconductor_war": [
                "https://news.google.com/rss/search?q=semiconductor+chip+ban+export+control+2025&hl=en-US&gl=US&ceid=US:en",
                "https://news.google.com/rss/search?q=TSMC+NVIDIA+chip+war+2025&hl=en-US&gl=US&ceid=US:en",
                "https://news.google.com/rss/search?q=chip+factory+fab+US+China+2025&hl=en-US&gl=US&ceid=US:en",
                "https://news.google.com/rss/search?q=ASML+chip+equipment+export+2025&hl=en-US&gl=US&ceid=US:en",
                "https://news.google.com/rss/search?q=advanced+semiconductor+restriction+2025&hl=en-US&gl=US&ceid=US:en",
            ],
            "39_ai_race": [
                "https://news.google.com/rss/search?q=AI+race+US+China+regulation+2025&hl=en-US&gl=US&ceid=US:en",
                "https://news.google.com/rss/search?q=OpenAI+DeepSeek+Gemini+LLM+2025&hl=en-US&gl=US&ceid=US:en",
                "https://news.google.com/rss/search?q=AI+military+weapon+surveillance+2025&hl=en-US&gl=US&ceid=US:en",
                "https://news.google.com/rss/search?q=AI+governance+ban+EU+AI+Act+2025&hl=en-US&gl=US&ceid=US:en",
                "https://news.google.com/rss/search?q=AI+chip+compute+power+2025&hl=en-US&gl=US&ceid=US:en",
            ],
            "40_critical_minerals": [
                "https://news.google.com/rss/search?q=critical+minerals+lithium+cobalt+2025&hl=en-US&gl=US&ceid=US:en",
                "https://news.google.com/rss/search?q=rare+earth+China+export+ban+2025&hl=en-US&gl=US&ceid=US:en",
                "https://news.google.com/rss/search?q=graphite+gallium+germanium+supply+2025&hl=en-US&gl=US&ceid=US:en",
                "https://news.google.com/rss/search?q=mineral+mine+Africa+Congo+supply+2025&hl=en-US&gl=US&ceid=US:en",
                "https://news.google.com/rss/search?q=EV+battery+mineral+shortage+2025&hl=en-US&gl=US&ceid=US:en",
            ],
            "41_disinformation": [
                "https://news.google.com/rss/search?q=disinformation+deepfake+propaganda+2025&hl=en-US&gl=US&ceid=US:en",
                "https://news.google.com/rss/search?q=election+interference+influence+operation+2025&hl=en-US&gl=US&ceid=US:en",
                "https://news.google.com/rss/search?q=fake+news+information+warfare+state+media+2025&hl=en-US&gl=US&ceid=US:en",
                "https://news.google.com/rss/search?q=social+media+manipulation+bot+network+2025&hl=en-US&gl=US&ceid=US:en",
                "https://news.google.com/rss/search?q=press+freedom+journalist+censorship+2025&hl=en-US&gl=US&ceid=US:en",
            ],
            "42_water_wars": [
                "https://news.google.com/rss/search?q=water+crisis+conflict+shortage+2025&hl=en-US&gl=US&ceid=US:en",
                "https://news.google.com/rss/search?q=Nile+dam+GERD+Ethiopia+Egypt+2025&hl=en-US&gl=US&ceid=US:en",
                "https://news.google.com/rss/search?q=Mekong+river+dam+China+2025&hl=en-US&gl=US&ceid=US:en",
                "https://news.google.com/rss/search?q=Indus+water+treaty+India+Pakistan+2025&hl=en-US&gl=US&ceid=US:en",
                "https://news.google.com/rss/search?q=groundwater+depletion+aquifer+drought+2025&hl=en-US&gl=US&ceid=US:en",
            ],
            "43_cryptocurrency": [
                "https://news.google.com/rss/search?q=bitcoin+crypto+market+2025&hl=en-US&gl=US&ceid=US:en",
                "https://news.google.com/rss/search?q=crypto+regulation+ban+law+2025&hl=en-US&gl=US&ceid=US:en",
                "https://news.google.com/rss/search?q=stablecoin+CBDC+digital+currency+2025&hl=en-US&gl=US&ceid=US:en",
                "https://news.google.com/rss/search?q=crypto+hack+fraud+exchange+2025&hl=en-US&gl=US&ceid=US:en",
                "https://news.google.com/rss/search?q=ethereum+bitcoin+crash+rally+2025&hl=en-US&gl=US&ceid=US:en",
            ],
            "44_grid_infrastructure": [
                "https://news.google.com/rss/search?q=power+grid+attack+blackout+2025&hl=en-US&gl=US&ceid=US:en",
                "https://news.google.com/rss/search?q=pipeline+sabotage+infrastructure+attack+2025&hl=en-US&gl=US&ceid=US:en",
                "https://news.google.com/rss/search?q=undersea+cable+cut+internet+2025&hl=en-US&gl=US&ceid=US:en",
                "https://news.google.com/rss/search?q=GPS+jamming+satellite+attack+2025&hl=en-US&gl=US&ceid=US:en",
                "https://news.google.com/rss/search?q=critical+infrastructure+hack+sabotage+2025&hl=en-US&gl=US&ceid=US:en",
            ],
        }

        total = 0
        for element_key, urls in topic_feeds.items():
            count = 0
            for url in urls:
                headlines = self._rss_headlines(url, 30)
                for text in headlines:
                    self._categorize_new(text)
                    self._categorize(text)
                    count += 1
                    total += 1
                time.sleep(0.2)
            print(f"   → [{element_key}] {count} headlines processed")

        print(f"   → Total country/topic headlines: {total}")

    # ──────────────────────────────────────────────────────────────────────────
    # 3. GDELT — real-time geopolitical event database
    # ──────────────────────────────────────────────────────────────────────────
    def fetch_gdelt_data(self):
        print("🌐 [GDELT] Fetching real-time geopolitical events...")
        try:
            url = (
                "https://api.gdeltproject.org/api/v2/doc/doc"
                "?query=conflict+war+sanction+protest+election"
                "&mode=timelinevol&format=json"
                f"&startdatetime={self.month_start.strftime('%Y%m%d%H%M%S')}"
                f"&enddatetime={self.now.strftime('%Y%m%d%H%M%S')}"
                "&smoothing=0"
            )
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                series = data.get("timeline", [{}])[0].get("data", [])
                if series:
                    recent_vals = [pt.get("value", 0) for pt in series[-7:]]
                    avg_intensity = float(np.mean(recent_vals)) if recent_vals else 0
                    boost = min(40, int(avg_intensity / 2))
                    for el in ["1_war_conflict","10_sanctions","7_protests_unrest","20_terrorism"]:
                        self._add_score(el, boost)
                    self.elements["1_war_conflict"]["indicators"].append(
                        f"GDELT conflict volume (7-day avg): {round(avg_intensity,1)}"
                    )
                    print(f"   → GDELT conflict intensity: {round(avg_intensity,1)}")
        except Exception as ex:
            print(f"   ⚠️  GDELT timeline failed: {ex}")

        # GDELT article list — country/conflict specific
        gdelt_queries = [
            ("india+border+conflict+trade",     ["32_india"]),
            ("usa+military+sanction+congress",  ["33_usa"]),
            ("china+taiwan+pla+military",       ["34_china"]),
            ("russia+ukraine+kremlin",          ["35_russia"]),
            ("iran+israel+houthi+middle+east",  ["36_middle_east"]),
            ("africa+coup+mineral+china",       ["37_africa"]),
            ("semiconductor+chip+ban+export",   ["38_semiconductor_war"]),
            ("artificial+intelligence+ai+race", ["39_ai_race"]),
            ("rare+earth+lithium+cobalt",       ["40_critical_minerals"]),
            ("power+grid+pipeline+sabotage",    ["44_grid_infrastructure"]),
        ]

        for query, elements in gdelt_queries:
            try:
                url2 = (
                    "https://api.gdeltproject.org/api/v2/doc/doc"
                    f"?query={query}&mode=artlist&format=json&maxrecords=20"
                    f"&startdatetime={self.month_start.strftime('%Y%m%d%H%M%S')}"
                    f"&enddatetime={self.now.strftime('%Y%m%d%H%M%S')}"
                )
                r2 = requests.get(url2, timeout=15)
                if r2.status_code == 200:
                    articles = r2.json().get("articles", [])
                    for art in articles[:10]:
                        title = art.get("title", "")
                        if title:
                            self._categorize_new(title)
                            self._categorize(title)
                            for el in elements:
                                self._add_score(el, 3)
                time.sleep(0.3)
            except Exception as ex:
                print(f"   ⚠️  GDELT artlist [{query[:30]}] failed: {ex}")

        print("   → GDELT country queries complete")

    # ──────────────────────────────────────────────────────────────────────────
    # 4. FRED API — current month economic indicators (optional free key)
    # ──────────────────────────────────────────────────────────────────────────
    def fetch_fred_data(self):
        print("📊 [FRED] Fetching economic indicators...")
        if FRED_API_KEY == "YOUR_FRED_API_KEY":
            print("   ⚠️  No FRED key — skipping (get free: fred.stlouisfed.org)")
            return

        series_map = {
            "CPIAUCSL":         ("2_inflation",      "US CPI (monthly)",            8.0),
            "CPILFESL":         ("2_inflation",      "US Core CPI",                 5.0),
            "FEDFUNDS":         ("22_interest_rates","Fed Funds Rate",               0),
            "UNRATE":           ("25_labor_strikes", "US Unemployment %",            0),
            "DCOILWTICO":       ("11_energy_crisis", "WTI Crude Oil Price",          0),
            "DHHNGSP":          ("11_energy_crisis", "Natural Gas Price",            0),
            "GOLDAMGBD228NLBM": ("23_commodity_prices","Gold Price",                 0),
            "T10YIE":           ("2_inflation",      "10yr Inflation Expectations",  3.0),
            "DTWEXBGS":         ("33_usa",           "US Dollar Index (broad)",      0),
            "INDPRO":           ("33_usa",           "US Industrial Production",     0),
        }
        obs_start = self.month_start.strftime("%Y-%m-%d")

        for series_id, (element, label, alert_threshold) in series_map.items():
            try:
                url = (
                    f"https://api.stlouisfed.org/fred/series/observations"
                    f"?series_id={series_id}&api_key={FRED_API_KEY}"
                    f"&observation_start={obs_start}&file_type=json"
                    f"&sort_order=desc&limit=5"
                )
                r = requests.get(url, timeout=10)
                if r.status_code == 200:
                    obs = r.json().get("observations", [])
                    vals = [float(o["value"]) for o in obs if o["value"] not in (".", "")]
                    if vals:
                        latest = vals[0]
                        self.elements[element]["indicators"].append(f"{label}: {round(latest,2)}")
                        self._add_score(element, 8)
                        if alert_threshold and latest > alert_threshold:
                            self.alerts.append(f"⚠️  {label} = {round(latest,2)} (above {alert_threshold})")
                        if element == "2_inflation":
                            self.elements["2_inflation"]["countries"].append(f"{label}: {round(latest,2)}")
                        if element == "22_interest_rates":
                            self.elements["22_interest_rates"]["central_banks"].append(
                                f"Fed Funds Rate: {round(latest,2)}%"
                            )
                time.sleep(0.15)
            except Exception as ex:
                print(f"   ⚠️  FRED {series_id}: {ex}")

        print("   → FRED indicators collected")

    # ──────────────────────────────────────────────────────────────────────────
    # 5. EIA — Weekly energy prices (optional free key)
    # ──────────────────────────────────────────────────────────────────────────
    def fetch_eia_data(self):
        print("⚡ [EIA] Fetching energy data...")
        endpoints = {
            "WTI Crude (weekly)":   "https://api.eia.gov/v2/petroleum/pri/spt/data/?frequency=weekly&data[0]=value&sort[0][column]=period&sort[0][direction]=desc&length=4",
            "Natural Gas (weekly)": "https://api.eia.gov/v2/natural-gas/pri/fut/data/?frequency=weekly&data[0]=value&sort[0][column]=period&sort[0][direction]=desc&length=4",
        }
        energy_data = {}
        for label, url in endpoints.items():
            try:
                full_url = url + (f"&api_key={EIA_API_KEY}" if EIA_API_KEY != "YOUR_EIA_API_KEY" else "")
                r = requests.get(full_url, timeout=12)
                if r.status_code == 200:
                    rows = r.json().get("response", {}).get("data", [])
                    if rows and len(rows) >= 2:
                        latest = float(rows[0]["value"])
                        prev   = float(rows[1]["value"])
                        change = ((latest - prev) / prev) * 100 if prev else 0
                        energy_data[label] = {"price": round(latest,2), "weekly_change_pct": round(change,2)}
                        self._add_score("11_energy_crisis", 8)
                        if abs(change) > 5:
                            self.alerts.append(f"⚠️  {label} moved {round(change,1)}% this week")
            except Exception as ex:
                print(f"   ⚠️  EIA {label}: {ex}")

        self.elements["11_energy_crisis"]["price_data"] = energy_data
        print(f"   → EIA data: {list(energy_data.keys()) or 'unavailable (set EIA_API_KEY)'}")

    # ──────────────────────────────────────────────────────────────────────────
    # 6. NASA EONET — Real-time natural disasters (current month)
    # ──────────────────────────────────────────────────────────────────────────
    def fetch_nasa_eonet(self):
        print("🌪️  [NASA EONET] Fetching natural disasters...")
        try:
            days_in_month = (self.now - self.month_start).days + 1
            url = f"https://eonet.gsfc.nasa.gov/api/v3/events?status=open&days={max(days_in_month,7)}&limit=50"
            r = requests.get(url, timeout=12)
            if r.status_code == 200:
                events = r.json().get("events", [])
                category_map = {
                    "Wildfires":        "15_climate_disasters",
                    "Floods":           "15_climate_disasters",
                    "Severe Storms":    "15_climate_disasters",
                    "Volcanoes":        "15_climate_disasters",
                    "Sea and Lake Ice": "15_climate_disasters",
                    "Drought":          "12_food_security",
                    "Dust and Haze":    "12_food_security",
                }
                counts = {}
                for event in events:
                    cats  = [c["title"] for c in event.get("categories", [])]
                    title = event.get("title", "")
                    for cat in cats:
                        el = category_map.get(cat, "15_climate_disasters")
                        self._add_score(el, 4)
                        self.elements[el].setdefault("events", []).append(title[:80])
                        counts[cat] = counts.get(cat, 0) + 1
                if len(events) > 20:
                    self.alerts.append(f"⚠️  {len(events)} active natural disaster events (NASA EONET)")
                print(f"   → {len(events)} active events | {counts}")
        except Exception as ex:
            print(f"   ⚠️  NASA EONET: {ex}")

    # ──────────────────────────────────────────────────────────────────────────
    # 7. USGS — Earthquakes current month M5.5+
    # ──────────────────────────────────────────────────────────────────────────
    def fetch_usgs_earthquakes(self):
        print("🌍 [USGS] Fetching earthquakes...")
        try:
            start = self.month_start.strftime("%Y-%m-%d")
            end   = self.now.strftime("%Y-%m-%d")
            url = (
                f"https://earthquake.usgs.gov/fdsnws/event/1/query"
                f"?format=geojson&starttime={start}&endtime={end}"
                f"&minmagnitude=5.5&orderby=magnitude&limit=20"
            )
            r = requests.get(url, timeout=12)
            if r.status_code == 200:
                feats = r.json().get("features", [])
                major = [f for f in feats if f["properties"]["mag"] >= 6.5]
                for f in feats[:5]:
                    p = f["properties"]
                    self.elements["15_climate_disasters"]["indicators"].append(
                        f"Earthquake M{p['mag']} — {p['place']}"
                    )
                self._add_score("15_climate_disasters", len(feats) * 2)
                if major:
                    self.alerts.append(f"⚠️  {len(major)} major earthquakes (M6.5+) this month")
                print(f"   → {len(feats)} quakes | {len(major)} major (M6.5+)")
        except Exception as ex:
            print(f"   ⚠️  USGS: {ex}")




    # ──────────────────────────────────────────────────────────────────────────
    # 8. Disease alerts — WHO + ProMED RSS (current month)
    # ──────────────────────────────────────────────────────────────────────────
    def fetch_disease_alerts(self):
        print("🦠 [WHO/ProMED] Fetching disease alerts...")
        feeds = [
            "https://www.who.int/rss-feeds/news-english.xml",
            "https://promedmail.org/feed/",
            "https://news.google.com/rss/search?q=disease+outbreak+epidemic+virus+alert&hl=en-US&gl=US&ceid=US:en",
        ]
        found = 0
        for url in feeds:
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries[:20]:
                    if not self._is_current_month(entry):
                        continue
                    text = (entry.get('title','') + " " + entry.get('summary','')).strip()
                    tl = text.lower()
                    if any(w in tl for w in ['disease','outbreak','virus','epidemic','alert','case','death','spread']):
                        self.elements["16_disease_outbreaks"]["alerts"].append(text[:100])
                        self._add_score("16_disease_outbreaks", 6)
                        self.elements["16_disease_outbreaks"]["mentions"] += 1
                        found += 1
            except Exception as ex:
                print(f"   ⚠️  Disease feed: {ex}")
        print(f"   → {found} disease alerts this month")

    # ──────────────────────────────────────────────────────────────────────────
    # 9. BLS — Labor data (no key, current year, latest month used)
    # ──────────────────────────────────────────────────────────────────────────
    def fetch_bls_data(self):
        print("👷 [BLS] Fetching labor data...")
        series = ["LNS14000000", "CES0000000001"]
        try:
            url     = "https://api.bls.gov/publicAPI/v1/timeseries/data/"
            payload = {"seriesid": series, "startyear": str(self.now.year), "endyear": str(self.now.year)}
            r = requests.post(url, json=payload, timeout=12)
            if r.status_code == 200:
                results = r.json().get("Results", {}).get("series", [])
                for series_data in results:
                    sid      = series_data.get("seriesID", "")
                    data_pts = series_data.get("data", [])
                    if data_pts:
                        latest = data_pts[0]
                        val    = latest.get("value","")
                        period = latest.get("periodName","")
                        year   = latest.get("year","")
                        label  = "Unemployment Rate" if "LNS" in sid else "Nonfarm Payrolls (thousands)"
                        self.elements["25_labor_strikes"]["indicators"].append(
                            f"{label}: {val} ({period} {year})"
                        )
                        self._add_score("25_labor_strikes", 5)
                        self.elements["25_labor_strikes"]["labor_data"][label] = f"{val} ({period} {year})"
                print("   → BLS labor data collected")
        except Exception as ex:
            print(f"   ⚠️  BLS: {ex}")

    # ──────────────────────────────────────────────────────────────────────────
    # 10. Commodities — yfinance period="1mo"
    # ──────────────────────────────────────────────────────────────────────────
    def fetch_commodity_data(self):
        print("📈 [yfinance] Fetching commodity prices...")
        if not YFINANCE_AVAILABLE:
            print("   ⚠️  yfinance not available"); return

        # FIXED TICKER: COBF.L changed to CC=F (Cocoa)
        symbols = {
            "Oil_WTI":   "USO", "Gold":       "GLD", "Silver":    "SLV",
            "Copper":    "CPER","Wheat":       "WEAT","Natural_Gas":"UNG",
            "Corn":      "CORN","Soybeans":   "SOYB","Lithium":   "LIT",
            "Uranium":   "URA", "Cobalt_ETF": "CC=F",
        }
        commodities = {}
        for name, sym in symbols.items():
            try:
                hist = yf.Ticker(sym).history(period="1mo")
                if not hist.empty and len(hist) >= 2:
                    cur  = float(hist['Close'].iloc[-1])
                    prev = float(hist['Close'].iloc[0])
                    chg  = ((cur - prev) / prev) * 100
                    commodities[name] = {"price": round(cur,2), "change_month_pct": round(chg,1)}
                   
                    self._add_score("23_commodity_prices", 3)
                   
                    if abs(chg) > 8:
                        direction = "up" if chg > 0 else "down"
                        self.alerts.append(f"⚠️  {name} {direction} {round(abs(chg),1)}% this month")
                        self._add_score("23_commodity_prices", 8)
                       
                    # cross-feed connections
                    if name in ("Oil_WTI","Natural_Gas"):
                        self._add_score("11_energy_crisis", 5 if abs(chg)>5 else 2)
                        self._add_score("35_russia", 4 if abs(chg)>5 else 1)
                        self._add_score("36_middle_east", 4 if abs(chg)>5 else 1)
                    if name in ("Wheat","Corn","Soybeans"):
                        self._add_score("12_food_security", 5 if abs(chg)>5 else 2)
                        self._add_score("37_africa", 3 if abs(chg)>5 else 1)
                    if name == "Uranium":
                        self._add_score("17_nuclear", 5 if abs(chg)>5 else 2)
                    if name in ("Lithium","Cobalt_ETF"):
                        self._add_score("40_critical_minerals", 6 if abs(chg)>5 else 2)
                        self._add_score("38_semiconductor_war", 3 if abs(chg)>5 else 1)
                time.sleep(0.1)
            except Exception:
                pass

        self.elements["23_commodity_prices"]["commodities"] = commodities
        print(f"   → {len(commodities)} commodities fetched")

    # ──────────────────────────────────────────────────────────────────────────
    # 11. Stock market — yfinance period="1mo"
    # ──────────────────────────────────────────────────────────────────────────
    def fetch_stock_market_data(self):
        print("📉 [yfinance] Fetching stock market data...")
        if not YFINANCE_AVAILABLE:
            print("   ⚠️  yfinance not available"); return

        # FIXED TICKER: Saudi_Tadawul updated to ^TASI.SR
        indices = {
            "S&P_500":       "^GSPC", "NASDAQ":       "^IXIC",
            "Dow_Jones":     "^DJI",  "VIX":          "^VIX",
            "UK_FTSE":       "^FTSE", "Germany_DAX":  "^GDAXI",
            "Japan_Nikkei":  "^N225", "India_Nifty":  "^NSEI",
            "HangSeng":      "^HSI",  "Brazil_Bovespa":"^BVSP",
            "Turkey_BIST":   "XU100.IS","Russia_MOEX": "IMOEX.ME",
            "Saudi_Tadawul": "^TASI.SR",
        }
        for name, sym in indices.items():
            try:
                hist = yf.Ticker(sym).history(period="1mo")
                if not hist.empty and len(hist) >= 2:
                    cur  = float(hist['Close'].iloc[-1])
                    prev = float(hist['Close'].iloc[0])
                    chg  = ((cur - prev) / prev) * 100
                    if name == "VIX":
                        self.elements["31_stock_market"]["volatility"] = round(cur, 2)
                    else:
                        self.elements["31_stock_market"]["indices"][name] = {
                            "current": round(cur,2), "change_month_pct": round(chg,1)
                        }
                        # feed country elements
                        if name == "India_Nifty":
                            self._add_score("32_india", 6 if abs(chg)>3 else 2)
                            self.elements["32_india"]["indicators"].append(f"Nifty50 MTD: {round(chg,1)}%")
                        if name in ("S&P_500","NASDAQ","Dow_Jones"):
                            self._add_score("33_usa", 5 if abs(chg)>3 else 2)
                        if name == "HangSeng":
                            self._add_score("34_china", 5 if abs(chg)>3 else 2)
                        if name == "Russia_MOEX":
                            self._add_score("35_russia", 5 if abs(chg)>3 else 2)
                           
                        if chg < -10:
                            self._add_score("31_stock_market", 15)
                            self.alerts.append(f"🔴 {name} down {round(chg,1)}% this month — crash risk")
                        elif chg < -5:
                            self._add_score("31_stock_market", 8)
                            self.alerts.append(f"⚠️  {name} correction: {round(chg,1)}% this month")
                time.sleep(0.1)
            except Exception:
                pass

        sectors = {
            "Technology":"XLK","Financial":"XLF","Energy":"XLE",
            "Healthcare":"XLV","Materials":"XLB","Utilities":"XLU",
            "Industrials":"XLI","Consumer":"XLY",
        }
        sec_perf = {}
        for sec, sym in sectors.items():
            try:
                hist = yf.Ticker(sym).history(period="1mo")
                if not hist.empty and len(hist) >= 2:
                    chg = ((float(hist['Close'].iloc[-1]) - float(hist['Close'].iloc[0])) / float(hist['Close'].iloc[0])) * 100
                    sec_perf[sec] = round(chg, 1)
                    # feed semiconductor/AI elements from tech sector
                    if sec == "Technology" and abs(chg) > 3:
                        self._add_score("38_semiconductor_war", 4)
                        self._add_score("39_ai_race", 4)
                time.sleep(0.1)
            except Exception:
                pass

        self.elements["31_stock_market"]["sector_performance"] = sec_perf

        sp  = self.elements["31_stock_market"]["indices"].get("S&P_500", {})
        chg = sp.get("change_month_pct", 0)
        vix = self.elements["31_stock_market"]["volatility"]
        if chg > 3:
            self.elements["31_stock_market"]["trend"] = "bullish"
        elif chg < -3:
            self.elements["31_stock_market"]["trend"] = "bearish"
        if vix > 30:
            self.alerts.append(f"🔴 VIX = {vix} — extreme fear / high volatility")
            self._add_score("31_stock_market", 15)
        elif vix > 20:
            self.alerts.append(f"⚠️  VIX = {vix} — elevated market anxiety")
        print(f"   → {len(self.elements['31_stock_market']['indices'])} indices | VIX: {vix}")

    # ──────────────────────────────────────────────────────────────────────────
    # 12. CRYPTOCURRENCY — CoinGecko public API (no key needed, current month)
    # ──────────────────────────────────────────────────────────────────────────
    def fetch_crypto_data(self):
        print("₿  [CoinGecko] Fetching crypto market data — current month...")
        coins = {
            "bitcoin":  "BTC",
            "ethereum": "ETH",
            "tether":   "USDT",
            "binancecoin": "BNB",
            "solana":   "SOL",
            "ripple":   "XRP",
        }
        coin_data = {}

        for coin_id, symbol in coins.items():
            try:
                # CoinGecko public endpoint — no key, 30 days = current month rolling
                url = (
                    f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
                    f"?vs_currency=usd&days=30&interval=daily"
                )
                r = requests.get(url, timeout=12, headers={"User-Agent": "Mozilla/5.0"})
                if r.status_code == 200:
                    prices = r.json().get("prices", [])
                    if len(prices) >= 2:
                        # Filter to current month only
                        month_ts = self.month_start.timestamp() * 1000
                        month_prices = [p for p in prices if p[0] >= month_ts]
                        if len(month_prices) >= 2:
                            price_start = month_prices[0][1]
                            price_end   = month_prices[-1][1]
                        else:
                            price_start = prices[0][1]
                            price_end   = prices[-1][1]

                        chg = ((price_end - price_start) / price_start) * 100 if price_start else 0
                        coin_data[symbol] = {
                            "price_usd":        round(price_end, 2),
                            "change_month_pct": round(chg, 1),
                        }
                       
                        self._add_score("43_cryptocurrency", 3)
                       
                        if abs(chg) > 20:
                            direction = "up" if chg > 0 else "down"
                            self.alerts.append(f"⚠️  {symbol} {direction} {round(abs(chg),1)}% this month")
                            self._add_score("43_cryptocurrency", 10)
                           
                        # high volatility in BTC feeds general financial stress
                        if coin_id == "bitcoin" and abs(chg) > 15:
                            self._add_score("31_stock_market", 5)
                           
                elif r.status_code == 429:
                    print(f"   ⚠️  CoinGecko rate limit hit — waiting 60s...")
                    time.sleep(60)
                time.sleep(1.5)   # respect CoinGecko free rate limit
            except Exception as ex:
                print(f"   ⚠️  CoinGecko {coin_id}: {ex}")

        self.elements["43_cryptocurrency"]["coins"] = coin_data
        print(f"   → {len(coin_data)} coins fetched")

    # ──────────────────────────────────────────────────────────────────────────
    # PATTERN DETECTION (original 10 + 10 new)
    # ──────────────────────────────────────────────────────────────────────────
    def detect_patterns(self):
        print("🔍 Detecting cross-element patterns...")
        e = self.elements

        checks = [
            # ── original patterns ──────────────────────────────────────────────
            (e["1_war_conflict"]["score"] > 30 and e["10_sanctions"]["score"] > 20,
             "War + Sanctions — escalating conflict cycle", True),
            (e["2_inflation"]["score"] > 30 and e["12_food_security"]["score"] > 20,
             "Inflation + Food stress — social unrest risk", False),
            (e["11_energy_crisis"]["score"] > 30 and e["24_supply_chains"]["score"] > 20,
             "Energy + Supply chain — industrial slowdown risk", False),
            (e["7_protests_unrest"]["score"] > 30 and e["5_elections"]["score"] > 20,
             "Elections + Protests — political instability window", False),
            (e["14_cyber_warfare"]["score"] > 20 and e["1_war_conflict"]["score"] > 30,
             "Cyber + Kinetic conflict — hybrid warfare pattern", True),
            (e["17_nuclear"]["score"] > 20 and e["19_diplomacy"]["score"] < 15,
             "Nuclear signals rising with low diplomacy — escalation risk", True),
            (e["16_disease_outbreaks"]["score"] > 20 and e["8_immigration"]["score"] > 20,
             "Disease + Migration — cross-border health risk", False),
            (e["2_inflation"]["score"] > 30 and e["22_interest_rates"]["score"] > 20,
             "Inflation + Rate pressure — central bank action likely", False),
            (e["13_debt_crisis"]["score"] > 20 and e["2_inflation"]["score"] > 30,
             "Debt + Inflation — sovereign stress risk", True),
            (e["31_stock_market"]["score"] > 40 or e["31_stock_market"]["volatility"] > 25,
             "Stock market stress / elevated volatility active", True),
            # ── new patterns ───────────────────────────────────────────────────
            (e["34_china"]["score"] > 30 and e["38_semiconductor_war"]["score"] > 25,
             "China pressure + Chip war — tech supply chain at risk", True),
            (e["33_usa"]["score"] > 30 and e["34_china"]["score"] > 30,
             "US-China tension elevated — global trade disruption risk", True),
            (e["35_russia"]["score"] > 30 and e["11_energy_crisis"]["score"] > 25,
             "Russia conflict + Energy crisis — European supply risk", True),
            (e["36_middle_east"]["score"] > 30 and e["11_energy_crisis"]["score"] > 25,
             "Middle East tensions + Energy — oil price spike risk", True),
            (e["40_critical_minerals"]["score"] > 25 and e["34_china"]["score"] > 25,
             "China mineral export controls — EV/Tech supply chain risk", True),
            (e["41_disinformation"]["score"] > 20 and e["5_elections"]["score"] > 20,
             "Disinformation + Elections — democratic process at risk", False),
            (e["44_grid_infrastructure"]["score"] > 20 and e["14_cyber_warfare"]["score"] > 20,
             "Grid attacks + Cyber — critical infrastructure under siege", True),
            (e["39_ai_race"]["score"] > 25 and e["38_semiconductor_war"]["score"] > 25,
             "AI race + Chip war — tech cold war intensifying", False),
            (e["42_water_wars"]["score"] > 20 and e["12_food_security"]["score"] > 20,
             "Water stress + Food insecurity — resource conflict likely", True),
            (e["32_india"]["score"] > 25 and (e["34_china"]["score"] > 25 or e["35_russia"]["score"] > 25),
             "India caught between major power tensions — strategic pressure", False),
            (e["43_cryptocurrency"]["score"] > 30 and e["31_stock_market"]["score"] > 30,
             "Crypto + Stock stress — broad financial market anxiety", False),
            (e["37_africa"]["score"] > 25 and e["40_critical_minerals"]["score"] > 25,
             "Africa instability + Mineral demand — supply security risk", True),
        ]

        for condition, message, is_alert in checks:
            if condition:
                self.patterns.append(message)
                if is_alert:
                    self.alerts.append(f"⚠️  Pattern: {message}")

    # ──────────────────────────────────────────────────────────────────────────
    # GENERATE OUTPUT JSON
    # ──────────────────────────────────────────────────────────────────────────
    def generate_output(self):
        active = []
        for name, data in self.elements.items():
            if data["score"] > 10:
                parts = name.split("_", 1)
                active.append({
                    "element":  f"{parts[0]}. {parts[1].replace('_',' ').upper()}",
                    "score":    int(data["score"]), # Cast back to clean int for output
                    "mentions": data.get("mentions", 0),
                })
        active.sort(key=lambda x: x["score"], reverse=True)

        return {
            "metadata": {
                "generated_at":  self.timestamp,
                "data_window":   "current_calendar_month_only",
                "month_start":   self.month_start.strftime("%Y-%m-%d"),
                "month_end":     self.now.strftime("%Y-%m-%d"),
                "total_elements": 44,
                "data_sources": [
                    "RSS: BBC, CNN, Al Jazeera, Reuters, Google News (15+ feeds)",
                    "RSS: Country/topic targeted feeds (60+ feeds)",
                    "GDELT (real-time geopolitics, no key)",
                    "NASA EONET (real-time disasters, no key)",
                    "USGS (real-time earthquakes, no key)",
                    "WHO/ProMED RSS (disease alerts, no key)",
                    "BLS public API v1 (labor, no key)",
                    "CoinGecko public API (crypto, no key)",
                    "yfinance (stocks + commodities, 1mo rolling)",
                    "FRED API (optional free key)",
                    "EIA API (optional free key)",
                ],
            },


   "summary": {
                "total_headlines":  self.news_headlines_count,
                "global_sentiment": self.avg_sentiment,
                "total_alerts":     len(self.alerts),
                "total_patterns":   len(self.patterns),
                "active_elements":  len(active),
            },
            "top_elements": active[:20],
            "all_elements": active,
            # ── financial data ────────────────────────────────────────────────
            "stock_market": {
                "indices":            self.elements["31_stock_market"]["indices"],
                "sector_performance": self.elements["31_stock_market"]["sector_performance"],
                "vix_volatility":     self.elements["31_stock_market"]["volatility"],
                "trend":              self.elements["31_stock_market"]["trend"],
            },
            "cryptocurrency":  self.elements["43_cryptocurrency"]["coins"],
            "commodities":     self.elements["23_commodity_prices"]["commodities"],
            "energy_prices":   self.elements["11_energy_crisis"]["price_data"],
            "inflation_data":  self.elements["2_inflation"]["countries"],
            "labor_data":      self.elements["25_labor_strikes"]["labor_data"],
            # ── geopolitical snapshots ────────────────────────────────────────
            "country_snapshots": {
                "india":       {"score": int(self.elements["32_india"]["score"]),
                                "top_signals": self.elements["32_india"]["indicators"][:5]},
                "usa":         {"score": int(self.elements["33_usa"]["score"]),
                                "top_signals": self.elements["33_usa"]["indicators"][:5]},
                "china":       {"score": int(self.elements["34_china"]["score"]),
                                "top_signals": self.elements["34_china"]["indicators"][:5]},
                "russia":      {"score": int(self.elements["35_russia"]["score"]),
                                "top_signals": self.elements["35_russia"]["indicators"][:5]},
                "middle_east": {"score": int(self.elements["36_middle_east"]["score"]),
                                "top_signals": self.elements["36_middle_east"]["indicators"][:5]},
                "africa":      {"score": int(self.elements["37_africa"]["score"]),
                                "top_signals": self.elements["37_africa"]["indicators"][:5]},
            },
            # ── new element snapshots ─────────────────────────────────────────
            "tech_war": {
                "semiconductor_score": int(self.elements["38_semiconductor_war"]["score"]),
                "ai_race_score":       int(self.elements["39_ai_race"]["score"]),
                "critical_minerals_score": int(self.elements["40_critical_minerals"]["score"]),
                "top_signals": (
                    self.elements["38_semiconductor_war"]["indicators"][:3] +
                    self.elements["39_ai_race"]["indicators"][:3]
                ),
            },
            "information_environment": {
                "disinformation_score": int(self.elements["41_disinformation"]["score"]),
                "top_signals": self.elements["41_disinformation"]["indicators"][:5],
            },
            "resource_wars": {
                "water_score":    int(self.elements["42_water_wars"]["score"]),
                "top_signals":    self.elements["42_water_wars"]["indicators"][:5],
            },
            "infrastructure_risk": {
                "grid_attack_score": int(self.elements["44_grid_infrastructure"]["score"]),
                "top_signals": self.elements["44_grid_infrastructure"]["indicators"][:5],
            },
            # ── alerts & patterns ─────────────────────────────────────────────
            "disease_alerts":  self.elements["16_disease_outbreaks"]["alerts"][:5],
            "critical_alerts": self.alerts[:15],
            "key_patterns":    self.patterns,

# ── composite risk scores (STRICT MATHEMATICAL AVERAGE) ───────────
            "risk_scores": {
                "geopolitical": min(100, int(sum([
                    self.elements["1_war_conflict"]["score"],
                    self.elements["10_sanctions"]["score"],
                    self.elements["17_nuclear"]["score"],
                    self.elements["20_terrorism"]["score"],
                ]) * 0.25)),
                "economic": min(100, int(sum([
                    self.elements["2_inflation"]["score"],
                    self.elements["13_debt_crisis"]["score"],
                    self.elements["31_stock_market"]["score"],
                    self.elements["11_energy_crisis"]["score"],
                ]) * 0.25)),
                "social": min(100, int(sum([
                    self.elements["7_protests_unrest"]["score"],
                    self.elements["25_labor_strikes"]["score"],
                    self.elements["8_immigration"]["score"],
                ]) * 0.33)),
                "environmental": min(100, int(sum([
                    self.elements["15_climate_disasters"]["score"],
                    self.elements["16_disease_outbreaks"]["score"],
                    self.elements["12_food_security"]["score"],
                ]) * 0.33)),
                "cyber_tech": min(100, int(sum([
                    self.elements["14_cyber_warfare"]["score"],
                    self.elements["27_tech_monopolies"]["score"],
                    self.elements["38_semiconductor_war"]["score"],
                    self.elements["39_ai_race"]["score"],
                ]) * 0.25)),
                "superpower_tension": min(100, int(sum([
                    self.elements["33_usa"]["score"],
                    self.elements["34_china"]["score"],
                    self.elements["35_russia"]["score"],
                ]) * 0.33)),
                "resource_security": min(100, int(sum([
                    self.elements["40_critical_minerals"]["score"],
                    self.elements["42_water_wars"]["score"],
                    self.elements["12_food_security"]["score"],
                ]) * 0.33)),
                "information_war": min(100, int(sum([
                    self.elements["41_disinformation"]["score"],
                    self.elements["44_grid_infrastructure"]["score"],
                ]) * 0.5)),
            },
            }


    # ──────────────────────────────────────────────────────────────────────────
    # RUN
    # ──────────────────────────────────────────────────────────────────────────
    def run(self):
        print("=" * 70)
        print("🌍 SENTINEL GLOBAL DATA COLLECTOR — 44 ELEMENTS")
        print(f"📅 Data window: {self.month_start.strftime('%Y-%m-%d')} → "
              f"{self.now.strftime('%Y-%m-%d')} (current month ONLY)")
        print("=" * 70)

        self.fetch_news_data()
        self.fetch_country_topic_feeds()
        self.fetch_gdelt_data()
        self.fetch_fred_data()
        self.fetch_eia_data()
        self.fetch_nasa_eonet()
        self.fetch_usgs_earthquakes()
        self.fetch_disease_alerts()
        self.fetch_bls_data()
        self.fetch_commodity_data()
        self.fetch_stock_market_data()
        self.fetch_crypto_data()
        self.detect_patterns()

        output = self.generate_output()

        with open("sentinel_44_summary.json", "w") as f:
            json.dump(output, f, indent=2)

        print("\n" + "=" * 70)
        print("✅ COLLECTION COMPLETE — ALL DATA IS CURRENT MONTH ONLY")
        print(f"📊 Headlines:           {self.news_headlines_count}")
        print(f"🔥 Active elements:     {output['summary']['active_elements']} / 44")
        print(f"📉 VIX:                 {output['stock_market']['vix_volatility']}")
        print(f"🌐 Sentiment:           {output['summary']['global_sentiment']}")
        print(f"⚠️  Alerts:              {output['summary']['total_alerts']}")
        print(f"🔗 Patterns:            {output['summary']['total_patterns']}")
        print(f"\n📊 RISK SCORES:")
        for domain, score in output["risk_scores"].items():
            bar = "█" * (score // 10) + "░" * (10 - score // 10)
            print(f"   {domain:<22} {bar} {score}")
        print(f"\n💾 Saved: sentinel_44_summary.json")
        print("=" * 70)
        print("\n📋 JSON OUTPUT:\n")
        print(json.dumps(output, indent=2))
        print("\n💡 Copy JSON above → paste into AI with your prediction prompt.")
        return output


# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n🚀 STARTING SENTINEL 44 — Global Event Collector (Current Month Only)\n")
    print("📦 Required:  pip install requests feedparser textblob numpy yfinance")
    print("🔑 Optional:  FRED key → fred.stlouisfed.org | EIA key → eia.gov/opendata\n")
    collector = Sentinel44Collector()
    collector.run()
    print("\n✅ Done! Check 'sentinel_44_summary.json'")
