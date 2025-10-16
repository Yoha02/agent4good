#!/usr/bin/env python3
"""
Simple runner for the EPA Air Quality Agent.
Windows-compatible version with proper encoding.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

from multi_tool_agent.agent import call_agent

def main():
    """Run the agent in interactive mode."""
    print("=" * 80)
    print("EPA AIR QUALITY AGENT - Interactive Mode")
    print("=" * 80)
    print("Ask questions about EPA air quality data from BigQuery!")
    print()
    print("Example queries:")
    print("  - What tables are in the EPA dataset?")
    print("  - Tell me about PM2.5 data")
    print("  - What was the air quality in Los Angeles in 2020?")
    print("  - Show me datasets available")
    print()
    print("Type 'quit', 'exit', or 'q' to exit.")
    print("=" * 80)
    print()
    
    while True:
        try:
            # Get user input
            user_input = input("Your question: ").strip()
            
            # Check for exit commands
            if user_input.lower() in ['quit', 'exit', 'q', '']:
                print("\nGoodbye! Thanks for using the EPA Air Quality Agent!")
                break
            
            # Process the query
            print("\nProcessing...")
            print("-" * 60)
            
            response = call_agent(user_input)
            
            print(f"\nAgent:")
            print(response)
            print("-" * 60)
            print()
            
        except KeyboardInterrupt:
            print("\n\nGoodbye! Thanks for using the EPA Air Quality Agent!")
            break
        except Exception as e:
            print(f"\n[ERROR] {str(e)}")
            print("Please try again or type 'quit' to exit.")
            print()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[FATAL ERROR] {str(e)}")
        import traceback
        traceback.print_exc()

