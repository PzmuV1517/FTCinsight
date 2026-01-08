# FTC Insight

FTC Insight is an open-source data analytics platform for FIRST Tech Challenge (FTC). We use the Expected Points Added (EPA) rating system to predict team performance and match outcomes. EPA builds upon the Elo rating system, but is directly in point units, separates into additional components, and has additional modifications that improve accuracy and calibration. FTC Insight computes both historical and realtime EPA results, and exposes data through a CSV export, REST API, Python package, and website.

<p width="100%" align="center">
  <img src="https://user-images.githubusercontent.com/16708871/212447884-68af251c-0813-4542-a81f-1a63c1388a69.png" width=400 />
</p>

## EPA Model

The Expected Points Added (EPA) model builds upon the Elo rating system, but transforms ratings to point units and makes several modifications. The EPA model was developed to provide a unified predictive system for FTC teams. At a high level, the EPA model converts Elo into point contributions, and then makes several modifications to improve accuracy and interpretability.

## Server

A FastAPI Python server integrates with the FTC Events API to compute, store, and serve EPA ratings. Seven SQL tables are created to aggregate results: `Teams`, `Years`, `TeamYears`, `Events`, `TeamEvents`, `Matches`, and `TeamMatches` (on CockroachDB). An internal API serves the frontend, while the REST API and Python API are made available for public use.

## FTC Events API Integration

FTC Insight uses the official FIRST Tech Challenge Events API to fetch team information, event details, match schedules, and scores. The API provides data for all official FTC events including:

- League Meets
- Qualifiers
- League Tournaments
- Championships
- Regional Championships
- FIRST Championships

## Python API

The Python API makes Expected Points Added (EPA) statistics just a few Python lines away! Currently we support queries on teams, years, events, and matches. Here's a short example demonstrating the package:

Install via

```bash
pip install ftcinsight
```

Then run

```python
import ftcinsight

ftc = ftcinsight.FTCInsight()
print(ftc.get_team(16461))  # Example FTC team number

>> {'team': 16461, 'name': 'Iron Reign', 'country': 'USA', 'state': 'TX', 'region': 'USTXNO', 'rookie_year': 2015, 'active': True, ...}
```

## Website

The website is written in NextJS, TypeScript, and TailwindCSS and aims to make EPA statistics accessible and actionable. The website includes EPA tables (with location filters, sortable columns), figures (Bubble charts, line graphs, bar graphs, etc.), live event simulation, match breakdowns (with component predictions), and more.

## Credits

This project is based on [Statbotics](https://statbotics.io), an FRC data analytics platform. FTC Insight adapts the same EPA methodology for FIRST Tech Challenge.

## Other

Feedback is always appreciated through GitHub issues.

If you are interested in contributing, please reach out through GitHub issues.

Thanks for your interest!
