🟢 INTRODUCTION AND DETAILS


This system is a Global Event Intelligence and Forecasting Framework built using Python and artificial intelligence. Its purpose is to collect large amounts of real-world information from around the globe, organize that information into meaningful categories, identify important patterns, and then use AI to generate forecasts about what may happen during the next 30 days.

The system works in two stages. The first stage is data collection and analysis using Python. The second stage is forecast generation using artificial intelligence.

In the first stage, Python acts as a massive global data collector. It automatically gathers information from many different public sources. These sources include international news feeds, geopolitical databases, economic databases, energy reports, natural disaster tracking systems, disease monitoring systems, labor statistics, commodity markets, and stock markets.

The system monitors 31 different elements that represent major forces affecting the world. These elements include war, conflict, inflation, trade disputes, military alliances, elections, scientific developments, protests, immigration, visa policies, sanctions, energy markets, food security, debt crises, cyber warfare, climate disasters, disease outbreaks, nuclear activity, space developments, diplomacy, terrorism, trade agreements, interest rates, supply chains, labor strikes, housing markets, technology regulation, demographics, religious tensions, corporate mergers, and stock market activity.

One of the most important features of the system is that it only uses data from the current calendar month. It intentionally ignores older information. This means the model focuses only on the most recent conditions and signals rather than historical events that may no longer be relevant.

The program starts by collecting thousands of news headlines from major international news organizations and specialized search feeds. It then examines the text and looks for keywords related to the 31 monitored elements. For example, if a headline contains words related to war, sanctions, cyberattacks, inflation, elections, or disease outbreaks, the system increases the score of the corresponding element.

The code also performs sentiment analysis. This helps determine whether the overall global news environment is positive, negative, or neutral. The result becomes part of the final intelligence summary.

Next, the program gathers geopolitical information from the GDELT database, which tracks global events and media activity in near real time. This helps the system measure the intensity of conflict, sanctions, protests, elections, terrorism, diplomacy, and other geopolitical developments.

The system then collects economic data from government databases. It monitors indicators related to inflation, interest rates, unemployment, and economic stress. It also tracks energy information such as oil and natural gas prices.

Another important part of the system is environmental monitoring. It collects data about active natural disasters from NASA and earthquake information from the USGS. This allows the model to measure environmental stress and disaster activity around the world.

The disease monitoring component collects information from global health organizations and outbreak alert systems. This helps detect unusual disease activity and public health risks.

The program also gathers financial information from stock markets and commodity markets. It monitors major stock indices, market volatility, sector performance, and the prices of important commodities such as oil, gold, silver, copper, wheat, natural gas, uranium, and agricultural products.

After collecting all this information, the system calculates scores for each of the 31 elements. A higher score means that particular area is showing more activity, stress, or importance during the current month.

The most powerful part of the code is the pattern detection engine. Instead of looking at individual events, it looks for relationships between different elements. For example, if war activity and sanctions are both elevated, the system identifies a possible escalation cycle. If cyber activity and military conflict are both elevated, it identifies a hybrid warfare pattern. If inflation and food stress are elevated together, it may identify a higher risk of social unrest. These relationships are much more valuable than looking at single events in isolation.

Once all calculations are complete, the Python program creates a compact JSON file. This JSON file contains only the most important information. Large amounts of raw data are compressed into a small, structured intelligence report. Instead of storing thousands of headlines and data points, it stores scores, alerts, patterns, risk levels, and key indicators.

The JSON file is then copied and pasted into an AI model together with a specialized forecasting prompt. The prompt instructs the AI not to summarize the news or repeat current events. Instead, it tells the AI to analyze the relationships between different elements and generate forecasts for the next 30 days.

The AI looks at the strongest signals, the highest-risk categories, and the detected cross-element patterns. It then produces original forecasts that estimate what is likely to happen next. Each forecast includes a probability percentage and a timeframe. The goal is not to predict exact events with certainty but to identify the most likely future developments based on current patterns.

For example, if conflict activity, sanctions, cyber activity, and energy stress are all elevated at the same time, the AI may forecast an increased likelihood of infrastructure disruptions, cyber incidents, or supply chain problems. These forecasts are generated through pattern recognition rather than by copying information from news articles.

The system therefore operates more like an intelligence analysis platform than a traditional news summarizer. It attempts to identify emerging risks, developing trends, and possible future scenarios before they become obvious.

The reason the system works is that major global events rarely occur in isolation. Wars affect energy markets. Energy markets affect inflation. Inflation affects social stability. Cyber activity can influence military conflicts. Disease outbreaks can affect migration and public policy. By monitoring many different elements simultaneously and examining how they interact, the system can identify patterns that may signal future developments.

However, it is important to understand that the forecasts are probabilities, not guarantees. The system estimates what is likely to happen based on current information. Unexpected events can always occur, and no forecasting model can predict the future with complete certainty.

In summary, this project combines large-scale data collection, pattern detection, risk analysis, and artificial intelligence forecasting. Python gathers and compresses current-month global data into a structured intelligence report, while AI analyzes that report to generate probability-based forecasts about what may happen during the next 30 days.


How to Use Sentinel-31

Using Sentinel-31 is simple and requires only two steps: data collection and AI forecasting.

First, copy the Python source code and run it in Python IDLE or any compatible Python environment. Once executed, the program automatically gathers current-month data from multiple global sources, including news feeds, geopolitical databases, economic indicators, energy markets, disease monitoring systems, natural disaster trackers, commodity markets, and stock market data.

The system processes this information across 31 major global elements and identifies important signals, alerts, and cross-element patterns. After analysis is complete, the program generates a compact JSON intelligence report named "global_31_elements_summary.json". This file contains a highly compressed representation of the collected data, making it efficient for AI analysis while preserving the most important information.

Next, copy the generated JSON output and paste it into an AI model together with the provided forecasting prompt. The AI is instructed not to summarize current events, repeat news headlines, or restate existing market data. Instead, it analyzes relationships between the 31 monitored elements and identifies emerging patterns that may indicate future developments.

Based on these patterns, the AI generates 5–7 original forecasts for the next 30 days. Each forecast includes a probability percentage, an estimated timeframe, and an explanation of which element combinations contributed to the prediction. The forecasts are intelligence-based assessments rather than news summaries and are designed to highlight potential future scenarios before they become widely recognized.

The entire workflow combines automated data collection, pattern detection, and AI-driven reasoning to transform large amounts of current global information into structured, probability-based forecasts. By focusing exclusively on current-month data, Sentinel-31 aims to provide timely and relevant insights into possible developments across geopolitical, economic, environmental, technological, and social domains.

🟢The Prompt is:


You are a predictive intelligence engine. Analyze this JSON data from my 31-element global event collector (all data from the LAST 30 DAYS ONLY).

DO NOT:
- Report current events or news headlines
- Summarize what already happened
- Restate any numbers (inflation, stock prices, etc.) as facts
- Use vague words like "a major," "a known," "a small," "a large," "some," "several," "a certain," "an unnamed"
- Use the phrase "a group" or "a hacker group" without naming who they work for

DO:
- Detect patterns across multiple elements
- Generate 5-7 ORIGINAL FORECASTS for events likely in the NEXT 30 DAYS
- Each forecast must be something NOT yet reported by any news source
- Assign probability (60-95%) and trigger timeframe (1-30 days)
- Explain which element combinations created each prediction

FORMAT RULES (MUST FOLLOW EVERY TIME):
- Start EVERY forecast with: "Within ___ days, [specific name] will [specific action]."
- Use ONLY future tense: will happen, will break, will declare, will raise, will freeze, will announce, will ambush
- NEVER use past tense (happened, was, occurred, reported)
- NEVER use present tense (is happening, are attacking)
- Write each forecast as ONE short sentence. Then a second sentence saying what happens next.
- Then write "Reason:" followed by ONE short sentence explaining why the data points to this.
- Then write "Probability: __%."
- Use very simple words. Write like you are explaining to a smart 14-year-old.

SPECIFICITY RULES (MOST IMPORTANT):
You MUST name at least ONE of these in every forecast:
- A specific country name (example: Germany, India, Brazil, Ukraine)
- A specific city name (example: Berlin, Mumbai, Sao Paulo, Lviv)
- A specific organization name (example: World Health Organization, Reserve Bank of India, NASA)
- A specific group name with country (example: Russia's Sandworm, North Korea's Lazarus)
- A specific person's title with country (example: Brazil's finance minister, India's RBI governor)

If you cannot pick ONE specific target from the data, then give TWO clear possibilities:
- Correct: "Either Germany's Gazprom pipeline or Poland's natural gas hub will..."
- Correct: "Either Russia's Roscosmos or China's CNSA will..."
- Wrong: "A space agency will..." (too vague)

REASON RULES:
- The reason must be ONE short sentence.
- The reason must name at least TWO elements from the data (example: "Cyber Warfare score 100 plus Energy Crisis score 100")
- The reason must explain WHY the timing is now (example: "Natural gas up 12.5% in last 30 days creates a target window")
- Do not write "because I think" or "because historically" — stick to what your data shows

TEST YOURSELF: After writing each forecast, ask: "Could I swap the target with a different country and the sentence still make sense?" If yes, rewrite it to be more specific.

EXAMPLE OF CORRECT OUTPUT:
"Within 18 days, Russia's Sandworm hacking group will shut down the natural gas pipeline control room outside Berlin, Germany. Heating for 200,000 homes will stop for three days. Reason: Cyber Warfare score 100 and Energy Crisis score 19 mentions, plus Natural Gas price jumped 12.5% creating a high-value target. Probability: 82%."

EXAMPLE OF WRONG OUTPUT (TOO VAGUE):
"Within 18 days, a known hacker group will attack something in Europe. Reason: because cyber is high. Probability: 80%."

The JSON contains recent 30-day data. Your job is to predict what comes NEXT.

Here is the data:

🟢WORKING EXAMPLE :

You are a predictive intelligence engine. Analyze this JSON data from my 31-element global event collector (all data from the LAST 30 DAYS ONLY).

DO NOT:
- Report current events or news headlines
- Summarize what already happened
- Restate any numbers (inflation, stock prices, etc.) as facts
- Use vague words like "a major," "a known," "a small," "a large," "some," "several," "a certain," "an unnamed"
- Use the phrase "a group" or "a hacker group" without naming who they work for

DO:
- Detect patterns across multiple elements
- Generate 5-7 ORIGINAL FORECASTS for events likely in the NEXT 30 DAYS
- Each forecast must be something NOT yet reported by any news source
- Assign probability (60-95%) and trigger timeframe (1-30 days)
- Explain which element combinations created each prediction

FORMAT RULES (MUST FOLLOW EVERY TIME):
- Start EVERY forecast with: "Within ___ days, [specific name] will [specific action]."
- Use ONLY future tense: will happen, will break, will declare, will raise, will freeze, will announce, will ambush
- NEVER use past tense (happened, was, occurred, reported)
- NEVER use present tense (is happening, are attacking)
- Write each forecast as ONE short sentence. Then a second sentence saying what happens next.
- Then write "Reason:" followed by ONE short sentence explaining why the data points to this.
- Then write "Probability: __%."
- Use very simple words. Write like you are explaining to a smart 14-year-old.

SPECIFICITY RULES (MOST IMPORTANT):
You MUST name at least ONE of these in every forecast:
- A specific country name (example: Germany, India, Brazil, Ukraine)
- A specific city name (example: Berlin, Mumbai, Sao Paulo, Lviv)
- A specific organization name (example: World Health Organization, Reserve Bank of India, NASA)
- A specific group name with country (example: Russia's Sandworm, North Korea's Lazarus)
- A specific person's title with country (example: Brazil's finance minister, India's RBI governor)

If you cannot pick ONE specific target from the data, then give TWO clear possibilities:
- Correct: "Either Germany's Gazprom pipeline or Poland's natural gas hub will..."
- Correct: "Either Russia's Roscosmos or China's CNSA will..."
- Wrong: "A space agency will..." (too vague)

REASON RULES:
- The reason must be ONE short sentence.
- The reason must name at least TWO elements from the data (example: "Cyber Warfare score 100 plus Energy Crisis score 100")
- The reason must explain WHY the timing is now (example: "Natural gas up 12.5% in last 30 days creates a target window")
- Do not write "because I think" or "because historically" — stick to what your data shows

TEST YOURSELF: After writing each forecast, ask: "Could I swap the target with a different country and the sentence still make sense?" If yes, rewrite it to be more specific.

EXAMPLE OF CORRECT OUTPUT:
"Within 18 days, Russia's Sandworm hacking group will shut down the natural gas pipeline control room outside Berlin, Germany. Heating for 200,000 homes will stop for three days. Reason: Cyber Warfare score 100 and Energy Crisis score 19 mentions, plus Natural Gas price jumped 12.5% creating a high-value target. Probability: 82%."

EXAMPLE OF WRONG OUTPUT (TOO VAGUE):
"Within 18 days, a known hacker group will attack something in Europe. Reason: because cyber is high. Probability: 80%."

The JSON contains recent 30-day data. Your job is to predict what comes NEXT.

Here is the data:






{
"metadata": {
"generated_at": "2026-05-30T16:46:13.899833Z",
"data_window": "current_calendar_month",
"month_start": "2026-05-01",
"data_sources": [
"RSS/News (15+ feeds)",
"GDELT (real-time)",
"FRED (monthly)",
"EIA (weekly)",
"NASA EONET (real-time)",
"USGS (real-time)",
"WHO/ProMED (real-time)",
"BLS (monthly)",
"yfinance (1mo)"
]
},
"summary": {
"total_headlines": 127,
"global_sentiment": 0.019,
"total_alerts": 8,
"total_patterns": 2,
"active_elements": 18
},
"top_elements": [
{
"element": "11. ENERGY CRISIS",
"score": 100,
"mentions": 19
},
{
"element": "14. CYBER WARFARE",
"score": 100,
"mentions": 20
},
{
"element": "15. CLIMATE DISASTERS",
"score": 100,
"mentions": 1
},
{
"element": "16. DISEASE OUTBREAKS",
"score": 100,
"mentions": 34
},
{
"element": "17. NUCLEAR",
"score": 100,
"mentions": 22
},
{
"element": "1. WAR CONFLICT",
"score": 95,
"mentions": 19
},
{
"element": "23. COMMODITY PRICES",
"score": 64,
"mentions": 2
},
{
"element": "25. LABOR STRIKES",
"score": 50,
"mentions": 8
},
{
"element": "18. SPACE RACE",
"score": 40,
"mentions": 8
},
{
"element": "20. TERRORISM",
"score": 40,
"mentions": 8
},
{
"element": "22. INTEREST RATES",
"score": 35,
"mentions": 7
},
{
"element": "2. INFLATION",
"score": 30,
"mentions": 6
},
{
"element": "5. ELECTIONS",
"score": 30,
"mentions": 6
},
{
"element": "6. SCIENCE TECH",
"score": 30,
"mentions": 6
},
{
"element": "10. SANCTIONS",
"score": 25,
"mentions": 5
}
],
"stock_market": {
"indices": {
"S&P_500": {
"current": 7580.06,
"change_month_pct": 5.1
},
"NASDAQ": {
"current": 26972.62,
"change_month_pct": 8.4
},
"Dow_Jones": {
"current": 51032.46,
"change_month_pct": 2.8
},
"UK_FTSE": {
"current": 10409.3,
"change_month_pct": 1.9
},
"Germany_DAX": {
"current": 25104.7,
"change_month_pct": 4.8
},
"Japan_Nikkei": {
"current": 66329.5,
"change_month_pct": 11.9
},
"India_Nifty": {
"current": 23547.75,
"change_month_pct": -2.6
},
"HangSeng": {
"current": 25182.39,
"change_month_pct": -3.6
},
"Brazil_Bovespa": {
"current": 173788.0,
"change_month_pct": -5.9
},
"Turkey_BIST": {
"current": 13662.8,
"change_month_pct": -4.5
}
},
"sector_performance": {
"Technology": 19.8,
"Financial": -1.1,
"Energy": -5.6,
"Healthcare": 2.4,
"Materials": -0.6,
"Utilities": -5.2,
"Industrials": -0.8,
"Consumer": 2.1
},
"vix_volatility": 15.32,
"trend": "bullish"
},
"commodities": {
"Oil_WTI": {
"price": 129.09,
"change_month_pct": -12.2
},
"Gold": {
"price": 417.12,
"change_month_pct": -1.5
},
"Silver": {
"price": 68.33,
"change_month_pct": 2.5
},
"Copper": {
"price": 38.86,
"change_month_pct": 6.4
},
"Wheat": {
"price": 23.38,
"change_month_pct": -3.0
},
"Natural_Gas": {
"price": 11.93,
"change_month_pct": 12.5
},
"Corn": {
"price": 17.93,
"change_month_pct": -4.1
},
"Soybeans": {
"price": 25.15,
"change_month_pct": 1.6
},
"Lithium": {
"price": 87.15,
"change_month_pct": -1.2
},
"Uranium": {
"price": 50.76,
"change_month_pct": -10.0
}
},
"energy_prices": {},
"inflation_data": [],
"labor_data": {
"Unemployment Rate": "4.3 (April 2026)",
"Nonfarm Payrolls (thousands)": "158736 (April 2026)"
},
"disease_alerts": [
"Experts convened by WHO advise on candidate treatments and vaccines for Ebola disease caused by Bund",
"Message by the WHO Director-General to the people of the Democratic Republic of the Congo <p>To the ",
"First meeting of the IHR Emergency Committee regarding the epidemic of Ebola Bundibugyo virus diseas",
"Seventy-ninth World Health Assembly honours global champions advancing primary health care <p>Today,",
"Director-General presents Award for Global Health to four distinguished leaders <p>At the Seventy-ni"
],
"critical_alerts": [
"\u26a0\ufe0f  50 active natural disaster events (NASA EONET)",
"\u26a0\ufe0f  3 major earthquakes (M6.5+) this month",
"\u26a0\ufe0f  Oil_WTI down 12.2% this month",
"\u26a0\ufe0f  Natural_Gas up 12.5% this month",
"\u26a0\ufe0f  Uranium down 10.0% this month",
"\u26a0\ufe0f  Brazil_Bovespa correction: -5.9% this month",
"\u26a0\ufe0f  Pattern: War + Sanctions \u2014 escalating conflict cycle",
"\u26a0\ufe0f  Pattern: Cyber + Kinetic conflict \u2014 hybrid warfare pattern"
],
"key_patterns": [
"War + Sanctions \u2014 escalating conflict cycle",
"Cyber + Kinetic conflict \u2014 hybrid warfare pattern"
],
"risk_scores": {
"geopolitical": 100,
"economic": 100,
"social": 75,
"environmental": 100,
"cyber_tech": 100
}
}




🟢DEEPSEEK AI RESPONSE:
Note=Always use deepseek ai because chatgpt is too conservative and don't give valuable results out.



Within 12 days, Russia’s Sandworm group will shut down a natural gas compressor station near Lviv, Ukraine. Power for 80,000 homes will fail for two days.
Reason: Cyber Warfare score 100 plus Energy Crisis score 19 mentions, and Natural Gas up 12.5% in 30 days makes energy infrastructure the top target.
Probability: 88%.

Within 8 days, North Korea’s Lazarus group will freeze the banking network of India’s National Payments Corporation in Mumbai. Digital payments will stop for 18 hours.
Reason: Cyber Warfare score 100 combined with War Conflict score 95, plus India_Nifty down 2.6% in a bullish global market creates a weak-point window.
Probability: 76%.

Within 15 days, the WHO will declare a new Ebola Bundibugyo virus outbreak in the Democratic Republic of the Congo. Three border towns will close crossings.
Reason: Disease Outbreaks score 100 with 34 mentions and WHO expert meetings on Ebola treatments in the last 30 days show active preparation for a real event.
Probability: 91%.

Within 20 days, Russia’s Roscosmos will announce a nuclear-powered space tug engine test failure. The test explosion will delay two planned lunar missions.
Reason: Nuclear score 100 and Space Race score 40, plus hybrid warfare pattern from Cyber + Kinetic conflict shows dual-use tech is under stress.
Probability: 69%.

Within 6 days, Brazil’s finance minister will freeze grain export taxes for soybeans from Sao Paulo state. Domestic food prices will drop 4% in two weeks.
Reason: Commodity Prices score 64 and Brazil_Bovespa down 5.9%, plus Soybeans up 1.6% and Wheat down 3.0% shows a regional food price imbalance needing action.
Probability: 74%.

Within 25 days, China’s CNSA will break a satellite refueling record at its Tiangong space station. The test will force two US commercial satellites to change orbit.
Reason: Space Race score 40 and Science Tech score 30, plus War Conflict score 95 and hybrid warfare pattern shows space is the next kinetic domain.
Probability: 65%.

Within 30 days, Turkey’s central bank will raise interest rates by 300 basis points in Istanbul. The Turkish lira will drop 8% against the US dollar in one week.
Reason: Interest Rates score 35 and Turkey_BIST down 4.5%, plus global bullish trend (S&P up 5.1%) makes Turkey’s divergence a forced correction point.
Probability: 82%.
