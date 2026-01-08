# FTC Insight API

FTC Insight aims to modernize FTC data analytics through developing and distributing cutting-edge metrics and analysis. This Python API makes Expected Points Added (EPA) statistics just a few Python lines away! Currently we support queries on teams, years, events, and matches. Read below for usage and documentation.

## Usage

With Python>=3.8 and pip installed, run

```
pip install ftcinsight
```

Then in a Python file, create an FTCInsight object and get started!

```python
import ftcinsight

ftc = ftcinsight.FTCInsight()
print(ftc.get_team(16461))

>> {'team': 16461, 'name': 'Iron Reign', 'country': 'USA', 'state': 'TX', 'region': 'USTXNO', 'rookie_year': 2015, 'active': True, ...}
```

Read below for more methods!

## API Reference

Documentation available in the docs folder.

## Contribute

If you are interested in contributing, please open an issue or pull request on GitHub.

## Support

If you are having issues, please let us know. We welcome issues and pull requests.

## License

The project is licensed under the MIT license.
