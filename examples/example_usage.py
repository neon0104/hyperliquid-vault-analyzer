import json
import sys
from analyzer import EnhancedVaultAnalyzer, predict_profit

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def load_config():
    """Load configuration from config.json"""
    with open("config.json", "r") as f:
        return json.load(f)

def main():
    # Load configuration
    config = load_config()
    user_address = config["account_address"]
    
    # Initialize analyzer
    analyzer = EnhancedVaultAnalyzer()
    
    print("\nAnalyzing vaults for user:", user_address)
    print("=" * 50)
    
    # Analyze vaults
    results = analyzer.analyze_vault(user_address=user_address)
    
    if results['status'] == 'success':
        data = results['data']
        
        print("\n[TOP] Top Performing Vaults (Ranked by Risk-Adjusted Returns):")
        print("=" * 70)
        
        for i, vault in enumerate(data['ranked_vaults'], 1):
            print(f"\n{i}. {vault['name']}")
            print(f"   +-- Predicted Monthly Return: {vault['predicted_return']:.2f}%")
            print(f"   +-- Risk Level: {vault['risk_level']}")
            print(f"   +-- Sharpe Ratio: {vault['sharpe_ratio']:.2f}")
            print(f"   +-- Recommended Allocation: {vault['recommended_allocation']:.1f}%")
        
        print("\n[PORTFOLIO] Portfolio Optimization Results:")
        print("=" * 50)
        print("Optimal allocation to maximize risk-adjusted returns:")
        for vault in data['ranked_vaults']:
            if vault['recommended_allocation'] > 1:
                print(f"  {vault['name']}: {vault['recommended_allocation']:.1f}%")
        
        # Example of profit prediction
        print("\n[PROFIT] Sample Profit Predictions:")
        print("=" * 50)
        investment = 10000  # Example investment amount
        apr = 20  # Example APR
        
        # Calculate different scenarios
        monthly_compound  = predict_profit(investment, apr, months=1, compounding=True)
        monthly_simple    = predict_profit(investment, apr, months=1, compounding=False)
        quarterly_compound = predict_profit(investment, apr, months=3, compounding=True)
        quarterly_simple  = predict_profit(investment, apr, months=3, compounding=False)
        
        print(f"\nFor ${investment:,.2f} investment at {apr}% APR:")
        print(f"  1 Month  (Compound) - Profit: ${monthly_compound:,.2f}  | Total: ${investment + monthly_compound:,.2f}")
        print(f"  1 Month  (Simple)   - Profit: ${monthly_simple:,.2f}  | Total: ${investment + monthly_simple:,.2f}")
        print(f"  3 Months (Compound) - Profit: ${quarterly_compound:,.2f} | Total: ${investment + quarterly_compound:,.2f}")
        print(f"  3 Months (Simple)   - Profit: ${quarterly_simple:,.2f} | Total: ${investment + quarterly_simple:,.2f}")
        
    else:
        print(f"Error: {results['message']}")

if __name__ == "__main__":
    main()
