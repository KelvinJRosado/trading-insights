This is a python project that analyzes current market conditions for cryptocurrency and provides insights into which coins might be good to invest in. 

The project requirements are as follows:
- The app uses python as the primary langauge
- At the start, only supports bitcoin, but the app should be designed to support additional coins in the future
- The app should have a sleek, modern design using industry standard libraries. It should look professional and be easy to use. Use dark mode by default, with an option to use light mode
- The app pulls the appropriate data related to the selected coin(s)
- The app uses whichever methods makes sense to make trading insights. THis could be a standard python library, an ML model, or whatever makes sense
- The app uses matplotlib to display its graphs
- The app should display a price graph for the selected coin. This should have options for the past 1 hour, 24 hours, or 7 days. THis should also be extensible if we want to add support for additional time ranges in the future
- The app should provide useful trading information for the asset. Information such as previous highs/low, indicators that it might be good to buy/sell, and current market conditions would all be helpful to have
- Include a section on screen for any relevant news articles about the coin. This should pull from any easily accessible free sources
- This should be a desktop GUI built with PyQt
- To start with, focus on the simple technical indicators, but make sure to make it expandable to allow ML-based inferences in the future

The development requirements are as follows:
- Use a venv
- Uses pip for package management, and pin dependencies to an exact version
- Make sure to commit often. We want many small commits rather than few large commits. The goal is to show gradual progression
- Start the project by designing a TODO list (saved as TODO.md), and update it as you complete the identified tasks
- If you are unsure of how to proceed on a given task, ask for input and provide options