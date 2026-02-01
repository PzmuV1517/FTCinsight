import React from "react";

import Link from "next/link";

export const metadata = {
  title: "Resources - FTC Insight",
};

const Page = () => {
  const posts = [
    {
      title: "Acknowledgments",
      lead: "FTC Insight is built upon the open-source Statbotics project. We thank the Statbotics team for making their code freely available for modification and reuse.",
      url: "/resources/acknowledgments",
      date: "2025-01-01",
    },
    {
      title: "The EPA Model",
      lead: "The Expected Points Added (EPA) model builds upon the Elo rating system, but transforms ratings to point units and makes several modifications.",
      url: "/resources/epa",
      date: "2023-01-09",
    },
    {
      title: "The EPA Model: A Gentle Introduction",
      lead: "The math behind EPA can be a bit confusing. This page will help you understand the EPA model, how it works, and how to best use it. No math required!",
      url: "/resources/intro",
      date: "2023-03-16",
    },
    {
      title: "Strength of Schedule",
      lead: "How can we use EPA to measure strength of schedule? We propose three metrics and briefly explore some results.",
      url: "/resources/sos",
      date: "2023-03-23",
    },
  ];

  return (
    <div className="w-full flex-grow">
      <div className="w-full h-full p-4 md:pt-8">
        <div className="w-full text-center text-3xl">Resources</div>
        <div className="grid lg:grid-cols-2 p-8">
          {posts.reverse().map((post) => (
            <div key={`post_${post.url}`} className="w-full p-2">
              <Link href={post.url}>
                <div className="w-full h-full p-8 rounded-lg bg-gray-100 hover:bg-blue-100">
                  <div className="w-full text-2xl">{post.title}</div>
                  <div className="w-full text-sm text-gray-500 mb-4">{post.date}</div>
                  <div className="w-full text-base">{post.lead}</div>
                </div>
              </Link>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Page;
