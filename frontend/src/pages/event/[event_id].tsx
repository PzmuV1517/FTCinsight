"use client";

import { useEffect, useState } from "react";

import { useRouter } from "next/router";

import { getEvent } from "../../api/event";
import SiteLayout from "../../layouts/siteLayout";
import Tabs from "../../pagesContent/event/[event_id]/tabs";
import NotFound from "../../pagesContent/shared/notFound";
import { EventData } from "../../types/data";
import { formatEventName } from "../../utils";

const InnerPage = () => {
  const router = useRouter();
  const { event_id } = router.query;

  const [data, setData] = useState<EventData | undefined>();

  useEffect(() => {
    const fetchEventData = async () => {
      if (!event_id || data?.event?.key == event_id) return;

      try {
        const eventData = await getEvent(event_id as string);
        setData(eventData);
      } catch (error) {
        console.error("Error fetching event data:", error);
      }
    };

    fetchEventData();
  }, [event_id, data]);

  useEffect(() => {
    if (event_id) {
      document.title = `${event_id} - FTC Insight`;
    }
  }, [event_id]);

  if (!data) {
    return <NotFound type="Event" />;
  }

  const truncatedEventName = formatEventName(data.event.name, 30);

  return (
    <div className="w-full h-full flex-grow flex flex-col pt-4 md:pt-8 md:pb-4 md:px-4">
      <div className="w-full flex flex-wrap items-center justify-center mb-4 gap-4">
        <p className="text-2xl lg:text-3xl max-w-full">
          {data.year.year} {truncatedEventName}
        </p>
      </div>
      <Tabs eventId={event_id as string} year={data.year.year} data={data} />
    </div>
  );
};

const Page = () => {
  return (
    <SiteLayout>
      <InnerPage />
    </SiteLayout>
  );
};
export default Page;
