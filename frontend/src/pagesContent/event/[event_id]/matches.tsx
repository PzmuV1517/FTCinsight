import React from "react";

import MatchTable from "../../../components/MatchTable";
import { EventData } from "../../../types/data";
import { round } from "../../../utils";

const MatchSection = ({ year, quals, data }: { year: number; quals: boolean; data: EventData }) => {
  const matches = data.matches.filter((match) => match.elim === !quals);

  const N = matches.filter((match) => match.status === "Completed").length;
  const correctPreds = matches
    .filter((match) => match.status === "Completed")
    .reduce((acc, match) => {
      if (match?.pred?.winner === match?.result?.winner) {
        return acc + 1;
      }
      return acc;
    }, 0);
  const accuracy = round((correctPreds / Math.max(N, 1)) * 100, 1);

  return (
    <div className="flex flex-col">
      <div className="w-full text-2xl font-bold mb-4">Match Predictions</div>
      <div>Remember, match predictions are just for fun, you control your own destiny!</div>
      {N > 0 && (
        <div>
          <strong>Accuracy: {accuracy}%</strong>
        </div>
      )}
      <div className="w-full my-4 overflow-x-scroll scrollbar-hide">
        <MatchTable year={data.event.year} teamNum={null} matches={matches} />
      </div>
    </div>
  );
};

export default MatchSection;
