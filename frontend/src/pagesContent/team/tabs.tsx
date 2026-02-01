"use client";

import React, { useMemo } from "react";

import { APITeam } from "../../types/api";
import { TeamYearData } from "../../types/data";
import TabsSection from "../shared/tabs";
import FigureSection from "./figures";
import OverviewSection from "./overview";

const Tabs = ({
  teamNum,
  year,
  teamYearData,
  fallbackTeamYearData,
}: {
  teamNum: number;
  year: number;
  teamYearData: TeamYearData | undefined;
  fallbackTeamYearData: TeamYearData | undefined;
}) => {
  const teamMatches = teamYearData?.team_matches ?? fallbackTeamYearData?.team_matches ?? [];
  const hasTeamData = teamYearData?.team_year || fallbackTeamYearData?.team_year;

  const MemoizedOverviewSection = useMemo(
    () => <OverviewSection teamYearData={teamYearData} />,
    [teamYearData]
  );

  const MemoizedFigureSection = useMemo(() => {
    // creates smooth transition
    const teamYear = teamYearData?.team_year ?? fallbackTeamYearData?.team_year;
    const matches = teamYearData?.team_matches ?? fallbackTeamYearData?.team_matches ?? [];
    return <FigureSection teamNum={teamNum} year={year} teamYear={teamYear} matches={matches} />;
  }, [teamNum, year, teamYearData, fallbackTeamYearData]);

  const tabs = [
    { title: "Overview", content: MemoizedOverviewSection },
    hasTeamData && { title: "Figures", content: MemoizedFigureSection },
  ].filter(Boolean);

  return <TabsSection loading={teamYearData === undefined} error={false} tabs={tabs} />;
};

export default Tabs;
