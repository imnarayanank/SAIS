"""
app/services/planner.py
------------------------
Pure-Python, lightweight machine learning and optimization models for the AI Study Planner.
Includes clustering (K-Means), regression, classification, RL (Q-Learning), and greedy scheduling.
"""
import math
import random
from datetime import datetime, timedelta

# --- 1. K-Means Clustering (Focus Clusters) ---
class KMeans:
    def __init__(self, k=3, max_iter=20):
        self.k = k
        self.max_iter = max_iter
        self.centroids = []

    def fit(self, data):
        """Data is list of [time_of_day_float, duration_hours]"""
        if not data:
            return []
        
        # Random initialization
        self.centroids = random.sample(data, min(self.k, len(data)))
        
        clusters = []
        for _ in range(self.max_iter):
            clusters = [[] for _ in range(self.k)]
            for point in data:
                distances = [self._dist(point, c) for c in self.centroids]
                idx = distances.index(min(distances))
                clusters[idx].append(point)
                
            new_centroids = []
            for i, cluster in enumerate(clusters):
                if not cluster:
                    new_centroids.append(self.centroids[i])
                    continue
                new_c = [sum(dim) / len(cluster) for dim in zip(*cluster)]
                new_centroids.append(new_c)
                
            if new_centroids == self.centroids:
                break
            self.centroids = new_centroids
        return clusters

    def _dist(self, p1, p2):
        return math.sqrt(sum((x - y) ** 2 for x, y in zip(p1, p2)))


# --- 2. Weighted Linear Regression (Task Duration Predictor) ---
class WeightedRegression:
    def __init__(self, lr=0.01, epochs=100):
        # [bias, estimated_time, difficulty, priority]
        self.w = [0.0, 1.0, 0.5, 0.1]
        self.lr = lr
        self.epochs = epochs

    def predict(self, x):
        return sum(wi * xi for wi, xi in zip(self.w, x))

    def fit(self, X, y, weights=None):
        if not X:
            return
        n = len(X)
        if weights is None:
            weights = [1.0] * n
            
        for _ in range(self.epochs):
            dw = [0.0] * len(self.w)
            for i in range(n):
                pred = self.predict(X[i])
                error = pred - y[i]
                for j in range(len(self.w)):
                    dw[j] += error * X[i][j] * weights[i]
            for j in range(len(self.w)):
                self.w[j] -= (self.lr / n) * dw[j]


# --- 3. Supervised Learning / Logistic Regression (Compliance Predictor) ---
class LogisticRegression:
    def __init__(self, lr=0.05, epochs=50):
        # [bias, hour_of_day, workload]
        self.w = [1.0, -0.05, -0.1]
        self.lr = lr
        self.epochs = epochs

    def sigmoid(self, z):
        return 1.0 / (1.0 + math.exp(-max(min(z, 20), -20)))

    def predict_proba(self, x):
        return self.sigmoid(sum(wi * xi for wi, xi in zip(self.w, x)))

    def fit(self, X, y):
        if not X:
            return
        n = len(X)
        for _ in range(self.epochs):
            dw = [0.0] * len(self.w)
            for i in range(n):
                pred = self.predict_proba(X[i])
                error = pred - y[i]
                for j in range(len(self.w)):
                    dw[j] += error * X[i][j]
            for j in range(len(self.w)):
                self.w[j] -= (self.lr / n) * dw[j]


# --- 4. Reinforcement Learning (Q-Learning slot preferences) ---
class SlotQLearning:
    def __init__(self, alpha=0.1, gamma=0.9):
        self.q_table = {}  # (day_of_week, hour) -> value
        self.alpha = alpha
        
    def get_q(self, day, hour):
        return self.q_table.get((day, hour), 0.5)  # Default neutral preference

    def update(self, day, hour, reward):
        # Reward 1.0 for completed session, -1.0 for missed
        current_q = self.get_q(day, hour)
        new_q = current_q + self.alpha * (reward - current_q)
        self.q_table[(day, hour)] = new_q


# --- 5. Global Model State Singleton ---
# In a real app this would be persisted to DB or saved per-user.
# We'll maintain a simple static store for demonstration.
class PlannerModels:
    def __init__(self):
        self.regression = WeightedRegression()
        self.classification = LogisticRegression()
        self.clustering = KMeans(k=2)
        self.rl = SlotQLearning()
        self.is_trained = False

global_models = PlannerModels()


# --- 6. Optimization / Constraint Satisfaction Scheduler ---
def generate_schedule(tasks, timetable_entries, start_date, days_ahead, max_daily_hours):
    """
    Schedule study sessions using greedy optimization considering predictions.
    """
    schedule = []
    
    # Sort tasks by priority (desc) and deadline (asc)
    tasks = sorted(tasks, key=lambda t: (-t.priority, t.deadline.timestamp() if t.deadline else 9999999999))
    
    current_date = start_date
    day_map = {0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday", 4: "Friday", 5: "Saturday", 6: "Sunday"}
    
    # Track hours scheduled per day to enforce max_daily_hours
    daily_hours_scheduled = {d: 0.0 for d in range(days_ahead)}
    
    for task in tasks:
        # Predict required duration using regression
        difficulty_score = {"Easy": 1, "Medium": 2, "Hard": 3}.get(task.difficulty, 2)
        x_reg = [1.0, task.estimated_time or 1.0, difficulty_score, task.priority or 3]
        predicted_duration = global_models.regression.predict(x_reg)
        predicted_duration = max(0.5, round(predicted_duration * 2) / 2.0)  # Round to nearest 0.5 hr
        
        hours_needed = predicted_duration
        
        # Greedily allocate time slots
        for day_offset in range(days_ahead):
            if hours_needed <= 0:
                break
                
            schedule_date = current_date + timedelta(days=day_offset)
            day_name = day_map[schedule_date.weekday()]
            
            # Constraints
            if daily_hours_scheduled[day_offset] >= max_daily_hours:
                continue
                
            if task.deadline and schedule_date > task.deadline.date():
                continue # Passed deadline
                
            # Find free slots by excluding timetable classes for this day
            classes_today = [c for c in timetable_entries if c.day == day_name]
            
            # Simple heuristic: Try 4 PM to 9 PM by default, or use RL preferences
            candidate_hours = [16, 17, 18, 19, 20, 21]
            # Sort by RL preference
            candidate_hours.sort(key=lambda h: global_models.rl.get_q(schedule_date.weekday(), h), reverse=True)
            
            for hour in candidate_hours:
                if hours_needed <= 0 or daily_hours_scheduled[day_offset] >= max_daily_hours:
                    break
                    
                start_time_str = f"{hour:02d}:00"
                end_time_str = f"{hour+1:02d}:00"
                
                # Check conflict with timetable
                conflict = False
                for c in classes_today:
                    if c.start_time and c.end_time:
                        if (c.start_time <= start_time_str < c.end_time) or (c.start_time < end_time_str <= c.end_time):
                            conflict = True
                            break
                            
                # Check conflict with already scheduled sessions
                for s in schedule:
                    if s["date"] == schedule_date.strftime("%Y-%m-%d"):
                        if (s["start_time"] <= start_time_str < s["end_time"]):
                            conflict = True
                            break
                            
                if not conflict:
                    # Predict compliance probability
                    # x_cls = [bias, hour_of_day, daily_workload]
                    x_cls = [1.0, float(hour), daily_hours_scheduled[day_offset]]
                    compliance_prob = global_models.classification.predict_proba(x_cls)
                    
                    schedule.append({
                        "task_id": task.task_id,
                        "task_title": task.title,
                        "course_name": task.course.name if task.course else "General",
                        "course_color": task.course.color if task.course and getattr(task.course, 'color', None) else "#4A90E2",
                        "date": schedule_date.strftime("%Y-%m-%d"),
                        "start_time": start_time_str,
                        "end_time": end_time_str,
                        "compliance_probability": round(compliance_prob, 2),
                        "difficulty": task.difficulty
                    })
                    hours_needed -= 1.0
                    daily_hours_scheduled[day_offset] += 1.0
                    
    return schedule
