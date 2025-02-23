"""Modern code features for dataset enhancement."""

modern_patterns = {
    "async_function": {
        "python": """
async def fetch_data(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()
""",
        "javascript": """
async function fetchData(url) {
    const response = await fetch(url);
    return await response.json();
}
"""
    },
    
    "destructuring": {
        "python": """
def process_user(user):
    name, age, *rest = user
    return {'name': name, 'age': age, 'other': rest}
""",
        "javascript": """
function processUser(user) {
    const [name, age, ...rest] = user;
    return {name, age, other: rest};
}
"""
    },
    
    "class_methods": {
        "python": """
class DataProcessor:
    def __init__(self, data):
        self.data = data
    
    @property
    def size(self):
        return len(self.data)
    
    @classmethod
    def from_json(cls, json_str):
        return cls(json.loads(json_str))
    
    def process(self):
        return [x * 2 for x in self.data]
""",
        "javascript": """
class DataProcessor {
    constructor(data) {
        this.data = data;
    }
    
    get size() {
        return this.data.length;
    }
    
    static fromJson(jsonStr) {
        return new DataProcessor(JSON.parse(jsonStr));
    }
    
    process() {
        return this.data.map(x => x * 2);
    }
}
"""
    },
    
    "generators": {
        "python": """
def fibonacci(n):
    a, b = 0, 1
    for _ in range(n):
        yield a
        a, b = b, a + b
""",
        "javascript": """
function* fibonacci(n) {
    let [a, b] = [0, 1];
    for (let i = 0; i < n; i++) {
        yield a;
        [a, b] = [b, a + b];
    }
}
"""
    },
    
    "type_hints": {
        "python": """
from typing import List, Dict, Optional

def search_users(
    users: List[Dict[str, str]],
    name: str,
    age: Optional[int] = None
) -> List[Dict[str, str]]:
    results = [u for u in users if name.lower() in u['name'].lower()]
    if age is not None:
        results = [u for u in results if u['age'] == age]
    return results
""",
        "javascript": """
/**
 * @param {Array<Object>} users
 * @param {string} name
 * @param {number?} age
 * @returns {Array<Object>}
 */
function searchUsers(users, name, age = null) {
    let results = users.filter(u => u.name.toLowerCase().includes(name.toLowerCase()));
    if (age !== null) {
        results = results.filter(u => u.age === age);
    }
    return results;
}
"""
    },
    
    "functional": {
        "python": """
def transform_data(data):
    return list(map(
        lambda x: {'id': x['id'], 'value': x['value'] * 2},
        filter(lambda x: x['value'] > 0, data)
    ))
""",
        "javascript": """
function transformData(data) {
    return data
        .filter(x => x.value > 0)
        .map(x => ({id: x.id, value: x.value * 2}));
}
"""
    },
    
    "error_handling": {
        "python": """
class ValidationError(Exception):
    pass

def validate_user(user):
    if not isinstance(user, dict):
        raise ValidationError("User must be a dictionary")
    if 'name' not in user:
        raise ValidationError("Name is required")
    if len(user['name']) < 2:
        raise ValidationError("Name is too short")
    return True
""",
        "javascript": """
class ValidationError extends Error {
    constructor(message) {
        super(message);
        this.name = 'ValidationError';
    }
}

function validateUser(user) {
    if (typeof user !== 'object' || user === null) {
        throw new ValidationError('User must be an object');
    }
    if (!user.name) {
        throw new ValidationError('Name is required');
    }
    if (user.name.length < 2) {
        throw new ValidationError('Name is too short');
    }
    return true;
}
"""
    }
}

# Additional patterns can be added here
web_patterns = {
    "dom_manipulation": {
        "python": """
# Using PyQt5/PySide2 for comparison
def update_ui(element_id, content):
    element = window.findChild(QWidget, element_id)
    if element:
        element.setText(content)
""",
        "javascript": """
function updateUI(elementId, content) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = content;
    }
}
"""
    },
    
    "event_handling": {
        "python": """
# Using PyQt5/PySide2 for comparison
def setup_button(button_id):
    button = window.findChild(QPushButton, button_id)
    button.clicked.connect(lambda: handle_click())
""",
        "javascript": """
function setupButton(buttonId) {
    const button = document.getElementById(buttonId);
    button.addEventListener('click', () => handleClick());
}
"""
    }
}
