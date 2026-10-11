import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

# Training dataset of typical financial transaction strings, tailored for Indian urban spending & global standards
TRAINING_DATA = [
    # Groceries (Indian & International)
    ("Blinkit Quick Grocery Delivery", "Groceries"),
    ("Zepto 10-Min Supermarket", "Groceries"),
    ("Instamart Swiggy Grocery Store", "Groceries"),
    ("BigBasket Daily Mart Superstore", "Groceries"),
    ("DMart Ready Hypermarket Retail", "Groceries"),
    ("Reliance Fresh Mart Vegetables", "Groceries"),
    ("Nature's Basket Organic Market", "Groceries"),
    ("Local Kirana Store Provisions", "Groceries"),
    ("More Retail Supermarket", "Groceries"),
    ("Fresh Produce Farmers Sabzi Mandi", "Groceries"),
    ("Walmart Supercenter", "Groceries"),
    ("Trader Joe's Market", "Groceries"),
    ("Whole Foods Market", "Groceries"),
    ("Costco Wholesale Grocery", "Groceries"),

    # Dining & Food Delivery
    ("Swiggy Food Delivery Order", "Dining"),
    ("Zomato Restaurant Delivery", "Dining"),
    ("Chai Point Tea Snacks Cafe", "Dining"),
    ("Blue Tokai Coffee Roasters", "Dining"),
    ("Barbeque Nation Buffet Dinner", "Dining"),
    ("Haldiram's Sweets and Restaurant", "Dining"),
    ("Saravana Bhavan Dosa Lunch", "Dining"),
    ("Bikanervala Sweets Snacks", "Dining"),
    ("Behrouz Biryani Royal Feast", "Dining"),
    ("Faasos Gourmet Wraps Delivery", "Dining"),
    ("Cafe Coffee Day Outpost", "Dining"),
    ("Starbucks Coffee #2841", "Dining"),
    ("Domino's Pizza Delivery", "Dining"),
    ("Chipotle Mexican Grill", "Dining"),
    ("McDonald's Fast Food", "Dining"),
    ("Subway Sandwiches Store", "Dining"),

    # Utilities & Bills
    ("Bescom Electricity Bill Bangalore", "Utilities"),
    ("Tata Power Mumbai Electricity", "Utilities"),
    ("MSEDCL Maharashtra Power Bill", "Utilities"),
    ("BWSSB Water Supply Board", "Utilities"),
    ("Delhi Jal Board Water Bill", "Utilities"),
    ("Airtel Xstream Fiber Broadband Bill", "Utilities"),
    ("Airtel Monthly WiFi Broadband", "Utilities"),
    ("Jio Fiber Broadband Internet", "Utilities"),
    ("Jio 5G Monthly Mobile Recharge", "Utilities"),
    ("Indane LPG Gas Cylinder Booking", "Utilities"),
    ("Bharat Gas Domestic LPG Cylinder", "Utilities"),
    ("Adani Electricity Power Bill", "Utilities"),
    ("ConEd Electric Utility Bill", "Utilities"),
    ("City Water & Sewer Department", "Utilities"),

    # Entertainment & Subscriptions
    ("BookMyShow PVR Cinemas Ticket", "Entertainment"),
    ("BookMyShow INOX Movies IMAX", "Entertainment"),
    ("Disney+ Hotstar Super Subscription", "Entertainment"),
    ("SonyLIV Monthly Stream Premium", "Entertainment"),
    ("Zee5 Premium Annual Entertainment", "Entertainment"),
    ("Netflix Monthly Subscription", "Entertainment"),
    ("Netflix Stream 4K", "Entertainment"),
    ("Spotify Premium Family Music", "Entertainment"),
    ("Spotify India Music Premium", "Entertainment"),
    ("Amazon Prime Video India", "Entertainment"),
    ("Steam Video Games Store", "Entertainment"),
    ("PlayStation Network Sony Store", "Entertainment"),

    # Salary & Income
    ("TCS Tata Consultancy Services Payroll Direct Deposit", "Salary"),
    ("Infosys Technologies Monthly Salary Credit", "Salary"),
    ("Wipro Limited Corporate Payroll", "Salary"),
    ("Tech Mahindra Monthly Salary Deposit", "Salary"),
    ("HCL Tech Corporate Paycheck", "Salary"),
    ("Google India Tech Salary Direct Deposit", "Salary"),
    ("Tech Corp Payroll Direct Deposit", "Salary"),
    ("Monthly Salary Direct Deposit", "Salary"),
    ("Bi-Weekly Paycheck Corporate Employer", "Salary"),
    ("ACH Credit Salary Payment", "Salary"),

    # Transport & Commute
    ("Ola Cabs City Ride Fare", "Transport"),
    ("Uber India Auto Go Trip", "Transport"),
    ("Rapido Bike Taxi Fare", "Transport"),
    ("Namma Metro Smart Card Recharge", "Transport"),
    ("Delhi Metro DMRC Smartcard Recharge", "Transport"),
    ("Indian Oil Petrol Pump Fuel IOCL", "Transport"),
    ("Bharat Petroleum Fuel Station BPCL", "Transport"),
    ("Hindustan Petroleum Auto HPCL", "Transport"),
    ("IRCTC Railway Express Ticket Booking", "Transport"),
    ("FASTag Highway Toll Recharge", "Transport"),
    ("Uber Ride Trip NYC", "Transport"),
    ("Lyft Express Transit", "Transport"),
    ("Shell Oil Gas Station #104", "Transport"),
]

class TransactionCategorizer:
    def __init__(self):
        self.pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(ngram_range=(1, 2), token_pattern=r'(?u)\b\w+\b', lowercase=True)),
            ('clf', LogisticRegression(C=5.0, max_iter=300))
        ])
        self._trained = False
        self._train()

    def _train(self):
        X = [item[0] for item in TRAINING_DATA]
        y = [item[1] for item in TRAINING_DATA]
        self.pipeline.fit(X, y)
        self._trained = True

    def predict(self, memo: str) -> dict:
        if not memo or not memo.strip():
            return {"category": "Entertainment", "confidence": 0.5, "fallback": True}

        cleaned = memo.strip()
        lower = cleaned.lower()
        keyword_rules = [
            # Groceries (Indian & Global)
            (r"\b(blinkit|zepto|instamart|bigbasket|dmart|d-mart|reliance fresh|nature's basket|kirana|sabzi|grocery|groceries|supermarket|market|walmart|kroger|safeway|costco|aldi|trader joe|whole foods)\b", "Groceries"),
            # Dining (Indian & Global)
            (r"\b(swiggy|zomato|chai point|blue tokai|barbeque nation|haldiram|saravana bhavan|bikanervala|behrouz|faasos|biryani|dosa|thali|samosa|starbucks|coffee|cafe|restaurant|diner|burger|pizza|mcdonald|chipotle|subway|taco|food|dining)\b", "Dining"),
            # Utilities (Indian & Global)
            (r"\b(bescom|tata power|msedcl|bwssb|delhi jal|airtel|jio|jiofiber|indane|bharat gas|adani|lpg|cylinder|recharge|electric|power|water|sewer|gas|utility|broadband|internet|verizon|wifi|cable)\b", "Utilities"),
            # Entertainment (Indian & Global)
            (r"\b(bookmyshow|pvr|inox|cinepolis|hotstar|sonyliv|zee5|netflix|spotify|hulu|disney|movie|cinema|amc|theatre|steam|game|playstation|xbox|music)\b", "Entertainment"),
            # Salary
            (r"\b(tcs|infosys|wipro|tech mahindra|hcl|salary|payroll|deposit|paycheck|wage|bonus|stipend)\b", "Salary"),
            # Transport (Indian & Global)
            (r"\b(ola|uber|rapido|namma metro|delhi metro|dmrc|indian oil|iocl|bharat petroleum|bpcl|hindustan petroleum|hpcl|irctc|fastag|petrol|diesel|cng|taxi|transit|metro|subway card|gas station|shell|chevron|exxon|bp|fuel|flight|airline|parking|toll)\b", "Transport"),
        ]

        for pattern, cat in keyword_rules:
            if re.search(pattern, lower):
                return {
                    "category": cat,
                    "confidence": 0.98,
                    "model": "nlp_hybrid_heuristic"
                }

        # Use scikit-learn model inference
        predicted_category = self.pipeline.predict([cleaned])[0]
        probabilities = self.pipeline.predict_proba([cleaned])[0]
        class_idx = list(self.pipeline.classes_).index(predicted_category)
        confidence = float(probabilities[class_idx])

        return {
            "category": predicted_category,
            "confidence": round(confidence, 3),
            "model": "tfidf_logistic_regression"
        }

# Global singleton
categorizer = TransactionCategorizer()

def predict_category(raw_memo: str) -> dict:
    return categorizer.predict(raw_memo)