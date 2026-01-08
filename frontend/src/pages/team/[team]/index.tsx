"use client";

import React, { useEffect } from "react";

import { useRouter } from "next/router";

import { CURR_YEAR } from "../../../constants";
import SiteLayout from "../../../layouts/siteLayout";
import PageContent from "../../../pagesContent/team/main";

const InnerPage = () => {
  const router = useRouter();
  const { team } = router.query;
  const paramYear = CURR_YEAR;

  useEffect(() => {
    if (team) {
      document.title = `Team ${team} - FTC Insight`;
    }
  }, [team]);

  // Wait for router to be ready
  if (!router.isReady || !team) {
    return <div>Loading...</div>;
  }

  return <PageContent team={Number(team)} paramYear={paramYear} />;
};

const Page = () => {
  return (
    <SiteLayout>
      <InnerPage />
    </SiteLayout>
  );
};

export default Page;
