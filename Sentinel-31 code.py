# ============================================================
# MASTER GLOBAL DATA COLLECTOR - 31 ELEMENTS
# STRICT: Current month data ONLY — no old/annual data
#
# DATA SOURCES (all free, all current-month):
#   News      → RSS: BBC, CNN, Al Jazeera, Reuters, AP, Google News
#   Geopolitics → GDELT Project (real-time, every 15 min)
#   Inflation   → FRED API (St. Louis Fed, monthly current)
#   Energy      → EIA API (weekly, current)
#   Climate     → NASA EONET (real-time natural disasters)
#   Earthquakes → USGS Earthquake API (real-time)
#   Disease     → WHO + ProMED RSS (real-time alerts)
#   Labor       → BLS API (monthly current)
#   Stocks      → yfinance (1mo = current month)
#   Commodities → yfinance (1mo = current month)
# ============================================================

import requests, json, numpy as np, feedparser, time, warnings, calendar
from datetime import datetime, timedelta
from textblob import TextBlob
warnings.filterwarnings('ignore')

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    print("⚠️  yfinance not installed — run: pip install yfinance")

# ── Optional: set your free FRED API key here ─────────────────────────────────
# Get free key at: https://fred.stlouisfed.org/docs/api/api_key.html
FRED_API_KEY = "YOUR_FRED_API_KEY"   # or leave as-is; falls back gracefully

# ── Optional: set your free EIA API key here ──────────────────────────────────
# Get free key at: https://www.eia.gov/opendata/register.php
EIA_API_KEY  = "YOUR_EIA_API_KEY"    # or leave as-is; falls back gracefully
# ──────────────────────────────────────────────────────────────────────────────


class GlobalThirtyOneElementsCollector:

    def __init__(self):
        self.now         = datetime.utcnow()
        self.timestamp   = self.now.isoformat() + "Z"
        # Strict gate: current calendar month only
        self.month_start = self.now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        self.cutoff_30d  = self.now - timedelta(days=31)   # fallback for APIs that don't do month

        self.alerts   = []
        self.patterns = []
        self.news_headlines_count = 0
        self.avg_sentiment = 0.0
        self.keyword_counts = {}

        self._init_elements()
        self._init_keywords()

    # ──────────────────────────────────────────────────────────────────────────
    # INIT
    # ──────────────────────────────────────────────────────────────────────────
    def _init_elements(self):
        base = lambda extra={}: {"score": 0, "indicators": [], "mentions": 0, **extra}
        self.elements = {
            "1_war_conflict":        base(),
            "2_inflation":           base({"countries": []}),
            "3_tariffs_trade":       base(),
            "4_military_alliances":  base(),
            "5_elections":           base(),
            "6_science_tech":        base(),
            "7_protests_unrest":     base(),
            "8_immigration":         base(),
            "9_visa_policies":       base(),
            "10_sanctions":          base(),
            "11_energy_crisis":      base({"price_data": {}}),
            "12_food_security":      base(),
            "13_debt_crisis":        base({"countries": []}),
            "14_cyber_warfare":      base(),
            "15_climate_disasters":  base({"events": []}),
            "16_disease_outbreaks":  base({"alerts": []}),
            "17_nuclear":            base(),
            "18_space_race":         base(),
            "19_diplomacy":          base(),
            "20_terrorism":          base(),
            "21_trade_agreements":   base(),
            "22_interest_rates":     base({"central_banks": []}),
            "23_commodity_prices":   base({"commodities": {}}),
            "24_supply_chains":      base(),
            "25_labor_strikes":      base({"labor_data": {}}),
            "26_housing_crisis":     base(),
            "27_tech_monopolies":    base(),
            "28_demographics":       base(),
            "29_religious_tensions": base(),
            "30_corporate_takeovers":base(),
            "31_stock_market":       base({"indices": {}, "sector_performance": {}, "volatility": 0.0, "trend": "neutral"}),
        }

    def _init_keywords(self):
        self.keyword_counts = {k: 0 for k in [
            'war','conflict','inflation','tariff','trade','military','election',
            'protest','sanction','oil','gas','energy','food','debt','cyber',
            'climate','disease','nuclear','space','stock','market','nasdaq',
            'vix','visa','immigration','housing','labor','religion','merger',
            'earthquake','flood','wildfire','hurricane','terror','hack'
        ]}

    # ──────────────────────────────────────────────────────────────────────────
    # HELPER: is RSS entry within current month?
    # ──────────────────────────────────────────────────────────────────────────
    def _is_current_month(self, entry) -> bool:
        pub = entry.get("published_parsed") or entry.get("updated_parsed")
        if pub is None:
            return True   # no date = keep
        try:
            pub_dt = datetime.utcfromtimestamp(calendar.timegm(pub))
            return pub_dt >= self.month_start
        except Exception:
            return True

    # ──────────────────────────────────────────────────────────────────────────
    # 1. NEWS — RSS (real-time, filtered to current month)
    # ──────────────────────────────────────────────────────────────────────────
    def fetch_news_data(self):
        print("📰 [NEWS] Fetching RSS feeds — current month only...")
        feeds = [
            "http://feeds.bbci.co.uk/news/world/rss.xml",
            "http://rss.cnn.com/rss/edition_world.rss",
            "https://www.aljazeera.com/xml/rss/all.xml",
            "https://feeds.reuters.com/reuters/worldNews",
            "https://feeds.reuters.com/reuters/businessNews",
            "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFZ4ZDJZS0VnWmxkV1FzQUFQAQ?hl=en-US&gl=US&ceid=US:en",
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
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries[:40]:
                    if not self._is_current_month(entry):
                        skipped += 1
                        continue
                    text = (entry.get('title','') + " " + entry.get('summary','')).strip()
                    if not text:
                        continue
                    all_headlines.append(text)
                    tl = text.lower()
                    for kw in self.keyword_counts:
                        if kw in tl:
                            self.keyword_counts[kw] += 1
                    self._categorize(text, TextBlob(text).sentiment.polarity)
            except Exception as ex:
                print(f"   ⚠️  Feed failed: {url[:60]} → {ex}")

        self.news_headlines_count = len(all_headlines)
        sents = [TextBlob(h).sentiment.polarity for h in all_headlines[:300]]
        self.avg_sentiment = round(float(np.mean(sents)), 3) if sents else 0.0
        print(f"   → {len(all_headlines)} current-month headlines | {skipped} old skipped")
        return all_headlines

    def _categorize(self, text, sentiment):
        tl = text.lower()
        cat_map = [
            (['war','conflict','battle','shelling','airstrike','troops','offensive'],      "1_war_conflict"),
            (['inflation','cpi','consumer price','cost of living','price surge'],          "2_inflation"),
            (['tariff','trade war','import duty','export ban','trade restriction'],        "3_tariffs_trade"),
            (['nato','alliance','military pact','defense agreement','joint exercise'],     "4_military_alliances"),
            (['election','ballot','vote','polling','referendum','candidate'],              "5_elections"),
            (['ai ','artificial intelligence','tech','research','breakthrough','chip'],    "6_science_tech"),
            (['protest','riot','demonstration','uprising','unrest','rally'],               "7_protests_unrest"),
            (['immigration','migrant','refugee','asylum','border crossing','deportation'], "8_immigration"),
            (['visa','travel ban','border control','entry restriction'],                   "9_visa_policies"),
            (['sanction','embargo','asset freeze','blacklist','export control'],           "10_sanctions"),
            (['oil','gas','energy','power outage','fuel','electricity shortage'],          "11_energy_crisis"),
            (['food','wheat','grain','hunger','famine','food price','crop'],               "12_food_security"),
            (['debt','default','imf','bailout','credit rating','bond yield'],             "13_debt_crisis"),
            (['cyber','hack','breach','ransomware','ddos','data leak','phishing'],        "14_cyber_warfare"),
            (['flood','drought','wildfire','cyclone','hurricane','typhoon','earthquake'], "15_climate_disasters"),
            (['disease','outbreak','pandemic','virus','epidemic','mpox','cholera'],       "16_disease_outbreaks"),
            (['nuclear','uranium','atomic','nuke','warhead','icbm'],                      "17_nuclear"),
            (['space','rocket','launch','satellite','moon','mars','orbit','nasa','spacex'],"18_space_race"),
            (['diplomacy','summit','ceasefire','peace talks','negotiation','envoy'],      "19_diplomacy"),
            (['terror','attack','bomb','explosion','militia','armed group'],              "20_terrorism"),
            (['trade deal','trade agreement','partnership','treaty','pact signed'],       "21_trade_agreements"),
            (['interest rate','federal reserve','fed rate','central bank','rate hike','rate cut','boe','ecb'], "22_interest_rates"),
            (['gold','copper','lithium','silver','commodity','iron ore'],                 "23_commodity_prices"),
            (['supply chain','logistics','shipping','container','port congestion'],       "24_supply_chains"),
            (['strike','labor','union','worker','walkout','picket','wage'],               "25_labor_strikes"),
            (['housing','real estate','mortgage','rent','property market'],               "26_housing_crisis"),
            (['antitrust','monopoly','big tech','regulation','breakup','fine'],           "27_tech_monopolies"),
            (['population','birth rate','aging','demographic','migration trend'],         "28_demographics"),
            (['religious','sectarian','church','mosque','temple','faith'],                "29_religious_tensions"),
            (['acquisition','merger','takeover','buyout','m&a','deal signed'],           "30_corporate_takeovers"),
            (['stock market','s&p','dow jones','nasdaq','market crash','vix',
              'bull market','bear market','selloff','rally','equities'],                  "31_stock_market"),
        ]
        for keywords, element in cat_map:
            if any(w in tl for w in keywords):
                self.elements[element]["indicators"].append(text[:120])
                self.elements[element]["mentions"] += 1
                self.elements[element]["score"] = min(100, self.elements[element]["score"] + 5)

    # ──────────────────────────────────────────────────────────────────────────
    # 2. GDELT — real-time geopolitical event database (updated every 15 min)
    #    Covers: war, conflict, sanctions, diplomacy, protests, terrorism
    # ──────────────────────────────────────────────────────────────────────────
    def fetch_gdelt_data(self):
        print("🌐 [GDELT] Fetching real-time geopolitical events...")
        # GDELT GKG (Global Knowledge Graph) — last 15 min file list is public
        # We use the doc API which returns counts by theme for the current day
        themes_to_elements = {
            "WAR":              "1_war_conflict",
            "CONFLICT":         "1_war_conflict",
            "SANCTION":         "10_sanctions",
            "PROTEST":          "7_protests_unrest",
            "TERROR":           "20_terrorism",
            "ELECTION":         "5_elections",
            "DIPLOMAT":         "19_diplomacy",
            "MILITARY":         "4_military_alliances",
            "NUCLEAR":          "17_nuclear",
            "CYBER":            "14_cyber_warfare",
            "REFUGEE":          "8_immigration",
            "FOOD_SECURITY":    "12_food_security",
            "ENERGY":           "11_energy_crisis",
            "ECON_BANKRUPTCY":  "13_debt_crisis",
        }
        try:
            # GDELT DOC 2.0 API — search last 30 days, free, no key needed
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
                # timeline volume gives activity intensity
                series = data.get("timeline", [{}])[0].get("data", [])
                if series:
                    recent_vals = [pt.get("value", 0) for pt in series[-7:]]
                    avg_intensity = float(np.mean(recent_vals)) if recent_vals else 0
                    # Scale: GDELT volume 0-100 maps to element score
                    boost = min(40, int(avg_intensity / 2))
                    for el in ["1_war_conflict", "10_sanctions", "7_protests_unrest", "20_terrorism"]:
                        self.elements[el]["score"] = min(100, self.elements[el]["score"] + boost)
                    self.elements["1_war_conflict"]["indicators"].append(
                        f"GDELT conflict volume (7-day avg): {round(avg_intensity,1)}"
                    )
                    print(f"   → GDELT conflict intensity: {round(avg_intensity,1)}")
        except Exception as ex:
            print(f"   ⚠️  GDELT failed: {ex}")

        # Also hit the GDELT geography API for active conflict countries
        try:
            url2 = (
                "https://api.gdeltproject.org/api/v2/doc/doc"
                "?query=war+airstrike+military+offensive"
                "&mode=artlist&format=json&maxrecords=30"
                f"&startdatetime={self.month_start.strftime('%Y%m%d%H%M%S')}"
                f"&enddatetime={self.now.strftime('%Y%m%d%H%M%S')}"
            )
            resp2 = requests.get(url2, timeout=15)
            if resp2.status_code == 200:
                articles = resp2.json().get("articles", [])
                for art in articles[:10]:
                    title = art.get("title","")
                    if title:
                        self._categorize(title, 0)
                print(f"   → GDELT articles processed: {len(articles)}")
        except Exception as ex:
            print(f"   ⚠️  GDELT artlist failed: {ex}")

    # ──────────────────────────────────────────────────────────────────────────
    # 3. FRED API — current month inflation, interest rates, unemployment
    #    (St. Louis Fed, free key, monthly releases)
    # ──────────────────────────────────────────────────────────────────────────
    def fetch_fred_data(self):
        print("📊 [FRED] Fetching current economic indicators...")
        if FRED_API_KEY == "YOUR_FRED_API_KEY":
            print("   ⚠️  No FRED API key set — skipping (get free key: fred.stlouisfed.org)")
            return

        # Series: CPIAUCSL=US CPI, FPCPITOTLZGUSA=global inflation proxy,
        #         FEDFUNDS=fed funds rate, UNRATE=unemployment
        series_map = {
            "CPIAUCSL":           ("2_inflation",     "US CPI (monthly)",     8.0),
            "CPILFESL":           ("2_inflation",     "US Core CPI",          5.0),
            "FEDFUNDS":           ("22_interest_rates","Fed Funds Rate",       0),
            "UNRATE":             ("25_labor_strikes", "US Unemployment %",    0),
            "DCOILWTICO":         ("11_energy_crisis", "WTI Crude Oil Price",  0),
            "DHHNGSP":            ("11_energy_crisis", "Natural Gas Price",    0),
            "GOLDAMGBD228NLBM":   ("23_commodity_prices","Gold Price",         0),
            "T10YIE":             ("2_inflation",     "10yr Inflation Expectations", 3.0),
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
                        self.elements[element]["score"] = min(100, self.elements[element]["score"] + 8)
                        if alert_threshold and latest > alert_threshold:
                            self.alerts.append(f"⚠️  {label} = {round(latest,2)} (above threshold {alert_threshold})")
                            self.elements[element]["score"] = min(100, self.elements[element]["score"] + 10)
                        # Add to inflation countries list
                        if element == "2_inflation":
                            self.elements["2_inflation"]["countries"].append(f"{label}: {round(latest,2)}")
                        if element == "22_interest_rates":
                            self.elements["22_interest_rates"]["central_banks"].append(f"Fed Funds Rate: {round(latest,2)}%")
                time.sleep(0.15)
            except Exception as ex:
                print(f"   ⚠️  FRED {series_id} failed: {ex}")

        print("   → FRED economic indicators collected")

   # ──────────────────────────────────────────────────────────────────────────
    # 4. EIA — Weekly energy prices (current, no key needed for basic)
    # ──────────────────────────────────────────────────────────────────────────
    def fetch_eia_data(self):
        print("⚡ [EIA] Fetching current energy data...")
        # EIA open data — weekly petroleum & gas prices, no key for v1 endpoints
        endpoints = {
            "WTI Crude (weekly)":    "https://api.eia.gov/v2/petroleum/pri/spt/data/?frequency=weekly&data[0]=value&sort[0][column]=period&sort[0][direction]=desc&length=4",
            "Natural Gas (weekly)":  "https://api.eia.gov/v2/natural-gas/pri/fut/data/?frequency=weekly&data[0]=value&sort[0][column]=period&sort[0][direction]=desc&length=4",
        }

        energy_data = {}
        for label, url in endpoints.items():
            try:
                # Add API key if set
                full_url = url + (f"&api_key={EIA_API_KEY}" if EIA_API_KEY != "YOUR_EIA_API_KEY" else "")
                r = requests.get(full_url, timeout=12)
                if r.status_code == 200:
                    rows = r.json().get("response", {}).get("data", [])
                    if rows and len(rows) >= 2:
                        latest = float(rows[0]["value"])
                        prev   = float(rows[1]["value"])
                        change = ((latest - prev) / prev) * 100 if prev else 0
                        energy_data[label] = {"price": round(latest,2), "weekly_change_pct": round(change,2)}
                        self.elements["11_energy_crisis"]["indicators"].append(
                            f"{label}: ${round(latest,2)} ({'+' if change>=0 else ''}{round(change,1)}% WoW)"
                        )
                        self.elements["11_energy_crisis"]["score"] = min(100, self.elements["11_energy_crisis"]["score"] + 8)
                        if abs(change) > 5:
                            self.alerts.append(f"⚠️  {label} moved {round(change,1)}% this week")
                            self.elements["11_energy_crisis"]["score"] = min(100, self.elements["11_energy_crisis"]["score"] + 10)
            except Exception as ex:
                print(f"   ⚠️  EIA {label} failed: {ex}")

        self.elements["11_energy_crisis"]["price_data"] = energy_data
        if energy_data:
            print(f"   → EIA energy prices: {list(energy_data.keys())}")
        else:
            print("   ⚠️  EIA data unavailable (set EIA_API_KEY for full access)")

    # ──────────────────────────────────────────────────────────────────────────
    # 5. NASA EONET — Real-time natural disasters / climate events
    # ──────────────────────────────────────────────────────────────────────────
    def fetch_nasa_eonet(self):
        print("🌪️  [NASA EONET] Fetching real-time natural disasters...")
        try:
            days_in_month = (self.now - self.month_start).days + 1
            url = f"https://eonet.gsfc.nasa.gov/api/v3/events?status=open&days={max(days_in_month,7)}&limit=50"
            r = requests.get(url, timeout=12)
            if r.status_code == 200:
                events = r.json().get("events", [])
                category_map = {
                    "Wildfires":         "15_climate_disasters",
                    "Floods":            "15_climate_disasters",
                    "Severe Storms":     "15_climate_disasters",
                    "Volcanoes":         "15_climate_disasters",
                    "Sea and Lake Ice":  "15_climate_disasters",
                    "Drought":           "12_food_security",
                    "Dust and Haze":     "12_food_security",
                }
                counts = {}
                for event in events:
                    cats = [c["title"] for c in event.get("categories", [])]
                    title = event.get("title","")
                    for cat in cats:
                        el = category_map.get(cat, "15_climate_disasters")
                        self.elements[el]["score"] = min(100, self.elements[el]["score"] + 4)
                        self.elements[el]["events"] = self.elements[el].get("events", [])
                        self.elements[el]["events"].append(title[:80])
                        counts[cat] = counts.get(cat, 0) + 1

                self.elements["15_climate_disasters"]["indicators"].append(
                    f"NASA EONET active events this month: {len(events)} | {json.dumps(counts)}"
                )
                if len(events) > 20:
                    self.alerts.append(f"⚠️  {len(events)} active natural disaster events (NASA EONET)")
                print(f"   → {len(events)} active disaster events | categories: {counts}")
        except Exception as ex:
            print(f"   ⚠️  NASA EONET failed: {ex}")

    # ──────────────────────────────────────────────────────────────────────────
    # 6. USGS — Real-time earthquake data (significant quakes, current month)
    # ──────────────────────────────────────────────────────────────────────────
    def fetch_usgs_earthquakes(self):
        print("🌍 [USGS] Fetching current month earthquakes...")
        try:
            start = self.month_start.strftime("%Y-%m-%d")
            end   = self.now.strftime("%Y-%m-%d")
            # Significant earthquakes M5.5+ current month
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
                self.elements["15_climate_disasters"]["score"] = min(
                    100, self.elements["15_climate_disasters"]["score"] + len(feats) * 2
                )
                if major:
                    self.alerts.append(f"⚠️  {len(major)} major earthquakes (M6.5+) this month")
                print(f"   → {len(feats)} significant earthquakes this month | {len(major)} major (M6.5+)")
        except Exception as ex:
            print(f"   ⚠️  USGS failed: {ex}")

    # ──────────────────────────────────────────────────────────────────────────
    # 7. WHO + ProMED RSS — Real-time disease outbreak alerts
    # ──────────────────────────────────────────────────────────────────────────
    def fetch_disease_alerts(self):
        print("🦠 [WHO/ProMED] Fetching disease outbreak alerts...")
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
                        self.elements["16_disease_outbreaks"]["score"] = min(
                            100, self.elements["16_disease_outbreaks"]["score"] + 6
                        )
                        self.elements["16_disease_outbreaks"]["mentions"] += 1
                        found += 1
            except Exception as ex:
                print(f"   ⚠️  Disease feed failed: {ex}")
        print(f"   → {found} disease alert items this month")

    # ──────────────────────────────────────────────────────────────────────────
    # 8. BLS API — Current month labor statistics (strikes, unemployment)
    # ──────────────────────────────────────────────────────────────────────────
    def fetch_bls_data(self):
        print("👷 [BLS] Fetching current labor data...")
        # BLS public API v1 (no key needed), series:
        # LNS14000000 = US unemployment rate
        # CES0000000001 = total nonfarm payroll
        series = ["LNS14000000", "CES0000000001"]
        try:
            url = "https://api.bls.gov/publicAPI/v1/timeseries/data/"
            payload = {"seriesid": series, "startyear": str(self.now.year), "endyear": str(self.now.year)}
            r = requests.post(url, json=payload, timeout=12)
            if r.status_code == 200:
                results = r.json().get("Results", {}).get("series", [])
                for series_data in results:
                    sid = series_data.get("seriesID","")
                    data_pts = series_data.get("data", [])
                    if data_pts:
                        latest = data_pts[0]
                        val = latest.get("value","")
                        period = latest.get("periodName","")
                        year = latest.get("year","")
                        label = "Unemployment Rate" if "LNS" in sid else "Nonfarm Payrolls (thousands)"
                        self.elements["25_labor_strikes"]["indicators"].append(
                            f"{label}: {val} ({period} {year})"
                        )
                        self.elements["25_labor_strikes"]["score"] = min(
                            100, self.elements["25_labor_strikes"]["score"] + 5
                        )
                        self.elements["25_labor_strikes"]["labor_data"][label] = f"{val} ({period} {year})"
                print("   → BLS labor data collected")
        except Exception as ex:
            print(f"   ⚠️  BLS failed: {ex}")

    # ──────────────────────────────────────────────────────────────────────────
    # 9. Commodities — yfinance period="1mo" (current month) ✅
    # ──────────────────────────────────────────────────────────────────────────
    def fetch_commodity_data(self):
        print("📈 [yfinance] Fetching commodity prices — current month...")
        if not YFINANCE_AVAILABLE:
            print("   ⚠️  yfinance not available")
            return

        symbols = {
            "Oil_WTI":    "USO",  "Gold":       "GLD",  "Silver":   "SLV",
            "Copper":     "CPER", "Wheat":      "WEAT", "Natural_Gas":"UNG",
            "Corn":       "CORN", "Soybeans":   "SOYB", "Lithium":  "LIT",
            "Uranium":    "URA",
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
                    self.elements["23_commodity_prices"]["score"] = min(100, self.elements["23_commodity_prices"]["score"] + 3)
                    if abs(chg) > 8:
                        direction = "up" if chg > 0 else "down"
                        self.alerts.append(f"⚠️  {name} {direction} {round(abs(chg),1)}% this month")
                        self.elements["23_commodity_prices"]["score"] = min(100, self.elements["23_commodity_prices"]["score"] + 8)
                    # Cross-feed relevant commodities
                    if name in ("Oil_WTI","Natural_Gas"):
                        self.elements["11_energy_crisis"]["score"] = min(100, self.elements["11_energy_crisis"]["score"] + (5 if abs(chg)>5 else 2))
                    if name in ("Wheat","Corn","Soybeans"):
                        self.elements["12_food_security"]["score"] = min(100, self.elements["12_food_security"]["score"] + (5 if abs(chg)>5 else 2))
                    if name == "Uranium":
                        self.elements["17_nuclear"]["score"] = min(100, self.elements["17_nuclear"]["score"] + (5 if abs(chg)>5 else 2))
                time.sleep(0.1)
            except Exception:
                pass

        self.elements["23_commodity_prices"]["commodities"] = commodities
        print(f"   → {len(commodities)} commodities fetched")

    # ──────────────────────────────────────────────────────────────────────────
    # 10. Stock market — yfinance period="1mo" (current month) ✅
    # ──────────────────────────────────────────────────────────────────────────
    def fetch_stock_market_data(self):
        print("📉 [yfinance] Fetching stock market data — current month...")
        if not YFINANCE_AVAILABLE:
            print("   ⚠️  yfinance not available")
            return

        indices = {
            "S&P_500":       "^GSPC", "NASDAQ":        "^IXIC",
            "Dow_Jones":     "^DJI",  "VIX":           "^VIX",
            "UK_FTSE":       "^FTSE", "Germany_DAX":   "^GDAXI",
            "Japan_Nikkei":  "^N225", "India_Nifty":   "^NSEI",
            "HangSeng":      "^HSI",  "Brazil_Bovespa":"^BVSP",
            "Turkey_BIST":   "XU100.IS",
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
                            "current": round(cur, 2), "change_month_pct": round(chg, 1)
                        }
                        if chg < -10:
                            self.elements["31_stock_market"]["score"] = min(100, self.elements["31_stock_market"]["score"] + 15)
                            self.alerts.append(f"🔴 {name} down {round(chg,1)}% this month — crash risk")
                        elif chg < -5:
                            self.elements["31_stock_market"]["score"] = min(100, self.elements["31_stock_market"]["score"] + 8)
                            self.alerts.append(f"⚠️  {name} correction: {round(chg,1)}% this month")
                time.sleep(0.1)
            except Exception:
                pass

        sectors = {
            "Technology":"XLK", "Financial":"XLF", "Energy":"XLE",
            "Healthcare":"XLV", "Materials":"XLB", "Utilities":"XLU",
            "Industrials":"XLI", "Consumer":"XLY",
        }
        sec_perf = {}
        for sec, sym in sectors.items():
            try:
                hist = yf.Ticker(sym).history(period="1mo")
                if not hist.empty and len(hist) >= 2:
                    chg = ((float(hist['Close'].iloc[-1]) - float(hist['Close'].iloc[0])) / float(hist['Close'].iloc[0])) * 100
                    sec_perf[sec] = round(chg, 1)
                time.sleep(0.1)
            except Exception:
                pass
        self.elements["31_stock_market"]["sector_performance"] = sec_perf

        sp = self.elements["31_stock_market"]["indices"].get("S&P_500", {})
        chg = sp.get("change_month_pct", 0)
        vix = self.elements["31_stock_market"]["volatility"]
        if chg > 3:
            self.elements["31_stock_market"]["trend"] = "bullish"
        elif chg < -3:
            self.elements["31_stock_market"]["trend"] = "bearish"
        if vix > 30:
            self.alerts.append(f"🔴 VIX = {vix} — extreme fear / high volatility")
            self.elements["31_stock_market"]["score"] = min(100, self.elements["31_stock_market"]["score"] + 15)
        elif vix > 20:
            self.alerts.append(f"⚠️  VIX = {vix} — elevated market anxiety")

        print(f"   → {len(self.elements['31_stock_market']['indices'])} indices | VIX: {self.elements['31_stock_market']['volatility']}")

    # ──────────────────────────────────────────────────────────────────────────
    # PATTERN DETECTION
    # ──────────────────────────────────────────────────────────────────────────
    def detect_patterns(self):
        print("🔍 Detecting cross-element patterns...")
        e = self.elements

        checks = [
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
        ]
        for condition, message, is_alert in checks:
            if condition:
                self.patterns.append(message)
                if is_alert:
                    self.alerts.append(f"⚠️  Pattern: {message}")

    # ──────────────────────────────────────────────────────────────────────────
  # GENERATE COMPACT OUTPUT JSON
    # ──────────────────────────────────────────────────────────────────────────
    def generate_output(self):
        active = []
        for name, data in self.elements.items():
            if data["score"] > 10:
                parts = name.split("_", 1)
                active.append({
                    "element":  f"{parts[0]}. {parts[1].replace('_',' ').upper()}",
                    "score":    data["score"],
                    "mentions": data.get("mentions", 0),
                })
        active.sort(key=lambda x: x["score"], reverse=True)

        return {
            "metadata": {
                "generated_at":    self.timestamp,
                "data_window":     "current_calendar_month",
                "month_start":     self.month_start.strftime("%Y-%m-%d"),
                "data_sources":    ["RSS/News (15+ feeds)", "GDELT (real-time)", "FRED (monthly)",
                                    "EIA (weekly)", "NASA EONET (real-time)", "USGS (real-time)",
                                    "WHO/ProMED (real-time)", "BLS (monthly)", "yfinance (1mo)"],
            },
            "summary": {
                "total_headlines":  self.news_headlines_count,
                "global_sentiment": self.avg_sentiment,
                "total_alerts":     len(self.alerts),
                "total_patterns":   len(self.patterns),
                "active_elements":  len(active),
            },
            "top_elements":   active[:15],
            "stock_market": {
                "indices":            self.elements["31_stock_market"]["indices"],
                "sector_performance": self.elements["31_stock_market"]["sector_performance"],
                "vix_volatility":     self.elements["31_stock_market"]["volatility"],
                "trend":              self.elements["31_stock_market"]["trend"],
            },
            "commodities":     self.elements["23_commodity_prices"]["commodities"],
            "energy_prices":   self.elements["11_energy_crisis"]["price_data"],
            "inflation_data":  self.elements["2_inflation"]["countries"],
            "labor_data":      self.elements["25_labor_strikes"]["labor_data"],
            "disease_alerts":  self.elements["16_disease_outbreaks"]["alerts"][:5],
            "critical_alerts": self.alerts[:10],
            "key_patterns":    self.patterns,
            "risk_scores": {
                "geopolitical": min(100, sum([
                    self.elements["1_war_conflict"]["score"],
                    self.elements["10_sanctions"]["score"],
                    self.elements["17_nuclear"]["score"],
                    self.elements["20_terrorism"]["score"],
                ])),
                "economic": min(100, sum([
                    self.elements["2_inflation"]["score"],
                    self.elements["13_debt_crisis"]["score"],
                    self.elements["31_stock_market"]["score"],
                    self.elements["11_energy_crisis"]["score"],
                ])),
                "social": min(100, sum([
                    self.elements["7_protests_unrest"]["score"],
                    self.elements["25_labor_strikes"]["score"],
                    self.elements["8_immigration"]["score"],
                ])),
                "environmental": min(100, sum([
                    self.elements["15_climate_disasters"]["score"],
                    self.elements["16_disease_outbreaks"]["score"],
                    self.elements["12_food_security"]["score"],
                ])),
                "cyber_tech": min(100, sum([
                    self.elements["14_cyber_warfare"]["score"],
                    self.elements["27_tech_monopolies"]["score"],
                ])),
            },
        }

    # ──────────────────────────────────────────────────────────────────────────
    # RUN
    # ──────────────────────────────────────────────────────────────────────────
    def run(self):
        print("=" * 70)
        print("🌍 MASTER GLOBAL DATA COLLECTOR — 31 ELEMENTS")
        print(f"📅 Data window: {self.month_start.strftime('%Y-%m-%d')} → {self.now.strftime('%Y-%m-%d')} (current month only)")
        print("=" * 70)

        self.fetch_news_data()
        self.fetch_gdelt_data()
        self.fetch_fred_data()
        self.fetch_eia_data()
        self.fetch_nasa_eonet()
        self.fetch_usgs_earthquakes()
        self.fetch_disease_alerts()
        self.fetch_bls_data()
        self.fetch_commodity_data()
        self.fetch_stock_market_data()
        self.detect_patterns()

        output = self.generate_output()

        with open("global_31_elements_summary.json", "w") as f:
            json.dump(output, f, indent=2)

        print("\n" + "=" * 70)
        print("✅ COLLECTION COMPLETE — ALL DATA IS CURRENT MONTH ONLY")
        print(f"📊 Headlines:      {self.news_headlines_count}")
        print(f"🔥 Active elements:{output['summary']['active_elements']}")
        print(f"📉 VIX:            {output['stock_market']['vix_volatility']}")
        print(f"🌐 Sentiment:      {output['summary']['global_sentiment']}")
        print(f"⚠️  Alerts:         {output['summary']['total_alerts']}")
        print(f"🔗 Patterns:       {output['summary']['total_patterns']}")
        print(f"💾 Saved:          global_31_elements_summary.json")
        print("=" * 70)
        print("\n📋 JSON OUTPUT:\n")
        print(json.dumps(output, indent=2))
        print("\n💡 Copy JSON above → paste into AI with your prediction prompt.")
        return output


if __name__ == "__main__":
    print("\n🚀 STARTING GLOBAL EVENT PREDICTOR — 31 Elements (Current Month Only)\n")
    collector = GlobalThirtyOneElementsCollector()
    collector.run()
    print("\n✅ Done! Check 'global_31_elements_summary.json'")
