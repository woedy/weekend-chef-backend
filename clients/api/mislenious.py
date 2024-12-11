# Predefined data
def create_default_dietary_preferences():
    preferences = [
        ('Vegetarian', 'Excludes meat and fish'),
        ('Vegan', 'Excludes all animal products'),
        ('Keto', 'High fat, low carbohydrate diet'),
        ('Gluten Free', 'Excludes gluten-containing grains'),
        ('Paleo', 'Mimics prehistoric human diet'),
        ('Halal', 'Complies with Islamic dietary laws'),
        ('Kosher', 'Complies with Jewish dietary laws'),
        ('Pescatarian', 'Includes fish, excludes other meats')
    ]
    
    for name, description in preferences:
        DietaryPreference.objects.get_or_create(
            name=name, 
            defaults={'description': description}
        )

def create_default_allergies():
    allergies = [
        ('Peanuts', 'High', 'Severe nut allergy'),
        ('Tree Nuts', 'High', 'Includes almonds, walnuts, etc.'),
        ('Dairy', 'Medium', 'Milk and milk products'),
        ('Eggs', 'Medium', 'Includes all egg products'),
        ('Soy', 'Low', 'Soy-based products'),
        ('Wheat', 'Medium', 'Gluten-containing grains'),
        ('Fish', 'High', 'All types of fish'),
        ('Shellfish', 'High', 'Shrimp, crab, lobster'),
        ('Sesame', 'Low', 'Sesame seeds and oil')
    ]
    
    for name, severity, description in allergies:
        Allergy.objects.get_or_create(
            name=name, 
            defaults={
                'severity': severity, 
                'description': description
            }
        )
