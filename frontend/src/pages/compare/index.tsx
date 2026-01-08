import React from "react";

import SiteLayout from "../../layouts/siteLayout";
import Tabs from "../../pagesContent/compare/tabs";

export const metadata = {
  title: "Compare Teams - FTC Insight",
};

const Page = () => {
  return (
    <SiteLayout>
      <Tabs />
    </SiteLayout>
  );
};

export default Page;
