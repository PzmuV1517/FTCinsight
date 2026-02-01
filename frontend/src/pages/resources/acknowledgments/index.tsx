import React from "react";

import Link from "next/link";

import PageLayout from "../../../layouts/blogLayout";

export const metadata = {
  title: "Acknowledgments - FTC Insight",
};

const Page = () => {
  return (
    <PageLayout
      title="Acknowledgments"
      lead="Thanking the open-source community that made FTC Insight possible"
    >
      <h3>Statbotics</h3>
      <p>
        FTC Insight is built upon the foundation of{" "}
        <Link
          className="text_link"
          rel="noopener noreferrer"
          target="_blank"
          href="https://github.com/avgupta456/statbotics"
        >
          Statbotics
        </Link>
        , an open-source project created by Abhijit Gupta. We are deeply grateful to the Statbotics
        team for making their code freely available under an open-source license, allowing projects
        like FTC Insight to adapt and extend their work for the FIRST Tech Challenge community.
      </p>
      <p>
        The EPA (Expected Points Added) model, data pipeline architecture, and many of the
        analytical concepts used in FTC Insight were originally developed for Statbotics. Their
        commitment to open-source software and advancing robotics analytics has been instrumental in
        making this project possible.
      </p>
      <h3>FIRST Inspires</h3>
      <p>
        We also thank{" "}
        <Link
          className="text_link"
          rel="noopener noreferrer"
          target="_blank"
          href="https://www.firstinspires.org/"
        >
          FIRST Inspires
        </Link>{" "}
        for providing the FTC Events API, which allows us to access match data and team information.
        Without their commitment to making competition data accessible, projects like this would not
        be possible.
      </p>
      <h3>Open Source</h3>
      <p>
        FTC Insight continues the tradition of open-source development. We encourage others to learn
        from, modify, and build upon this project to further advance the FTC community&apos;s access
        to analytical tools and insights.
      </p>
      <h3>Notes</h3>
      <p>
        This is a rather small acknowledgment page for now, but we plan to expand it in the future to include
        special thanks to the original creators of Statbotics.

        Once again love you guys! Amazing work, amazing code, an amazing project all around.
      </p>
    </PageLayout>
  );
};

export default Page;
