import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Route, Routes } from "react-router";

import { NewsArchivePage, NewsListPage } from "@modules/news-archieve";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      refetchOnReconnect: false,
      retry: 1
    }
  }
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Routes>
        <Route path="/" element={<NewsArchivePage />} />
        <Route path="/news" element={<NewsListPage />} />
      </Routes>
    </QueryClientProvider>
  )
}

export default App
