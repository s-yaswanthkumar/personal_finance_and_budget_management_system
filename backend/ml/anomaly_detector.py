import numpy as np
from sklearn.ensemble import IsolationForest
from backend.db.postgres import get_db_cursor

class TransactionAnomalyDetector:
    def __init__(self):
        self.model = IsolationForest(
            n_estimators=100,
            contamination=0.04,
            random_state=42
        )
        self._fitted = False
        self._baseline_amounts = []
        self._train_initial_baseline()

    def _train_initial_baseline(self):
        # Seed initial synthetic and typical transaction amounts
        typical_data = [
            # Regular expenses (amounts between $5 and $120)
            [round(x, 2), 12] for x in np.random.uniform(5.0, 120.0, size=200)
        ] + [
            # Occasional larger utilities or shopping (between $100 and $250)
            [round(x, 2), 15] for x in np.random.uniform(100.0, 250.0, size=50)
        ] + [
            # Known anomalies
            [1200.0, 3],
            [3500.0, 2],
            [5000.0, 1],
        ]
        X = np.array(typical_data)
        self.model.fit(X)
        self._fitted = True
        self._baseline_amounts = [row[0] for row in typical_data[:250]]

    def fit_user_history(self, user_id: int):
        """Optionally retrain using real user transaction history from PostgreSQL."""
        try:
            with get_db_cursor() as (cur, conn):
                cur.execute("""
                    SELECT amount, EXTRACT(HOUR FROM transaction_date) AS tx_hour
                    FROM transactions
                    WHERE user_id = %s AND transaction_type = 'expense'
                    ORDER BY transaction_date DESC
                    LIMIT 200;
                """, (user_id,))
                rows = cur.fetchall()
                if len(rows) >= 15:
                    X = np.array([[float(r[0]), float(r[1])] for r in rows])
                    self.model.fit(X)
                    self._baseline_amounts = [float(r[0]) for r in rows]
        except Exception:
            pass

    def detect(self, amount: float, tx_hour: int = 14, category: str = "General") -> dict:
        """
        Determines whether a transaction is anomalous.
        Returns:
            {
                "is_anomaly": bool,
                "score": float,
                "severity": str ("anomaly" or "normal"),
                "reason": str
            }
        """
        features = np.array([[amount, tx_hour]])
        pred = self.model.predict(features)[0]  # -1 for anomaly, 1 for normal
        score = float(self.model.decision_function(features)[0])

        avg_amount = np.mean(self._baseline_amounts) if self._baseline_amounts else 55.0
        ratio = amount / max(1.0, avg_amount)

        is_anomaly = False
        reason = "Normal spending pattern."

        # Flag if Isolation Forest says -1 OR amount is an extreme outlier (> 5x average and > $400)
        if pred == -1 or (amount > 400.0 and ratio > 4.0):
            is_anomaly = True
            reason = (
                f"Isolation Forest flagged anomaly (score: {round(score, 3)}). "
                f"Amount ${amount:,.2f} is {round(ratio, 1)}x higher than standard "
                f"spending average (${avg_amount:,.2f})."
            )

        return {
            "is_anomaly": is_anomaly,
            "score": round(score, 3),
            "ratio_to_mean": round(ratio, 2),
            "severity": "anomaly" if is_anomaly else "normal",
            "reason": reason
        }

# Global singleton
anomaly_detector = TransactionAnomalyDetector()

def detect_anomaly(amount: float, tx_hour: int = 14, category: str = "General") -> dict:
    return anomaly_detector.detect(amount, tx_hour, category)