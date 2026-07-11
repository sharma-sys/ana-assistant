"use client";

import React, { useState, useEffect, useRef } from 'react';
import SearchBar from '../components/SearchBar';
import StateCityFilters from '../components/StateCityFilters';
import NewsFeed from '../components/NewsFeed';
import AIPanel from '../components/AIPanel';
import Toast from '../components/Toast';
import { fetchNews, generateAIContent, triggerRSSFetch, fetchActiveSources, fetchTopGridNews, fetchPramukhSamachar, fetchFilters } from '../services/api';
import { NewsArticle, AIResult } from '../types';
import styles from './page.module.css';
import Image from 'next/image';
import useSWR from 'swr';

export default function Dashboard() {
  const [search, setSearch] = useState('');
  const [selectedState, setSelectedState] = useState('All');
  const [selectedCity, setSelectedCity] = useState('All');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [selectedSource, setSelectedSource] = useState('All');
  
  const [articles, setArticles] = useState<NewsArticle[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [isLoadingMore, setIsLoadingMore] = useState(false);

  const [generatingId, setGeneratingId] = useState<string | number | null>(null);
  const [aiResult, setAiResult] = useState<AIResult | null>(null);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'info' } | null>(null);

  const [activeChannels, setActiveChannels] = useState<{id: number, name: string}[]>([]);
  const [topGridArticles, setTopGridArticles] = useState<NewsArticle[]>([]);
  const [groupedNews, setGroupedNews] = useState<Record<string, NewsArticle[]>>({});

  // Real states & districts from backend (replaces static mockData)
  const [states, setStates] = useState<string[]>(['All']);
  const [cities, setCities] = useState<Record<string, string[]>>({ All: ['All'] });

  const categories = ['All', 'National', 'Regional', 'International', 'Sports', 'General'];

  const sidebarRef = useRef<HTMLDivElement>(null);
  const isHoveredRef = useRef(false);

  const { data: activeChannelsData } = useSWR('activeSources', fetchActiveSources);
  useEffect(() => { if (activeChannelsData) setActiveChannels(activeChannelsData); }, [activeChannelsData]);

  // Fetch real states & districts from backend on mount
  const { data: filtersData } = useSWR('sourceFilters', fetchFilters);
  useEffect(() => {
    if (filtersData) {
      setStates(filtersData.states);
      setCities(filtersData.districts);
    }
  }, [filtersData]);

  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        await triggerRSSFetch();
      } catch (error) {
        console.error("Failed to auto-sync RSS feeds", error);
      }
    }, 120000); 
    return () => clearInterval(interval);
  }, []);

  const [debouncedSearch, setDebouncedSearch] = useState('');
  useEffect(() => {
    const handler = setTimeout(() => { setDebouncedSearch(search); }, 300);
    return () => clearTimeout(handler);
  }, [search]);

  // Fetch all sections simultaneously so they refresh together
  const [isLoadingAll, setIsLoadingAll] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setIsLoadingAll(true);
    // Clear old data immediately so all sections go into loading state together
    setArticles([]);
    setTopGridArticles([]);
    setGroupedNews({});

    const fetchAll = async () => {
      try {
        // Use selectedCity for district filtering (district_news collector populates this field)
        const effectiveCity = selectedCity;
        const promises: Promise<unknown>[] = [
          fetchNews(debouncedSearch, selectedState, effectiveCity, selectedCategory, selectedSource, 1),
        ];
        if (selectedSource === 'All') {
          promises.push(
            fetchTopGridNews(debouncedSearch, selectedState, effectiveCity, selectedCategory),
            fetchPramukhSamachar(debouncedSearch, selectedState, effectiveCity, selectedCategory)
          );
        }
        const results = await Promise.all(promises);
        if (cancelled) return;

        const newsResult = results[0] as { articles: NewsArticle[], totalPages: number };
        setArticles(newsResult.articles);
        setTotalPages(newsResult.totalPages);
        setPage(1);

        if (selectedSource === 'All' && results.length === 3) {
          const topGrid = results[1] as NewsArticle[];
          const pramukh = results[2] as Record<string, NewsArticle[]>;
          setTopGridArticles(topGrid);
          const topIds = new Set(topGrid.map(a => a.id));
          const filteredPramukh: Record<string, NewsArticle[]> = {};
          Object.keys(pramukh).forEach(source => {
            const uniqueArts = pramukh[source].filter(a => !topIds.has(a.id)).slice(0, 5);
            if (uniqueArts.length > 0) filteredPramukh[source] = uniqueArts;
          });
          setGroupedNews(filteredPramukh);
        }
      } catch (error) {
        console.error('Failed to fetch news:', error);
      } finally {
        if (!cancelled) setIsLoadingAll(false);
      }
    };

    fetchAll();
    return () => { cancelled = true; };
  }, [debouncedSearch, selectedState, selectedCity, selectedCategory, selectedSource]);


  useEffect(() => {
    let animationFrameId: number;

    const scrollSidebar = () => {
      if (sidebarRef.current && !isHoveredRef.current && selectedSource === 'All') {
        sidebarRef.current.scrollTop += 1;
        
        // Loop back to top if reached bottom
        if (sidebarRef.current.scrollTop + sidebarRef.current.clientHeight >= sidebarRef.current.scrollHeight - 1) {
           sidebarRef.current.scrollTop = 0;
        }
      }
      animationFrameId = requestAnimationFrame(scrollSidebar);
    };

    animationFrameId = requestAnimationFrame(scrollSidebar);
    return () => cancelAnimationFrame(animationFrameId);
  }, [selectedSource]);

  const handleSearch = () => {
    // Search is handled by useEffect due to state changes
  };

  const handleLoadMore = async () => {
    if (page >= totalPages || isLoadingMore) return;
    setIsLoadingMore(true);
    const nextPage = page + 1;
    try {
      const { articles: moreArticles, totalPages: fetchedTotalPages } = await fetchNews(search, selectedState, selectedCity, selectedCategory, selectedSource, nextPage);
      setArticles(prev => [...prev, ...moreArticles]);
      setTotalPages(fetchedTotalPages);
      setPage(nextPage);
    } catch (error) {
      console.error("Failed to load more news", error);
    } finally {
      setIsLoadingMore(false);
    }
  };

  const handleGenerateAI = async (articleId: string | number) => {
    setGeneratingId(articleId);
    try {
      const result = await generateAIContent(articleId);
      setAiResult(result);
    } catch (error) {
      console.error("Failed to generate AI content", error);
      const errorMessage = error instanceof Error ? error.message : "Failed to generate AI content. Please try again.";
      setToast({ message: errorMessage, type: 'error' });
    } finally {
      setGeneratingId(null);
    }
  };

  const handleManualFetch = async () => {
    setToast({ message: 'Fetching latest news from RSS...', type: 'info' });
    try {
      const res = await triggerRSSFetch();
      setToast({ message: `Success! Fetched ${res.new_articles_count} new articles.`, type: 'success' });
      // Refresh the news feed
      const { articles: results, totalPages: fetchedTotalPages } = await fetchNews(search, selectedState, selectedCity, selectedCategory, selectedSource, 1);
      setArticles(results);
      setTotalPages(fetchedTotalPages);
      setPage(1);
    } catch (error) {
      console.error(error);
      setToast({ message: 'Failed to fetch RSS feeds.', type: 'error' });
    }
  };



  return (
    <main className={styles.main}>
      <header className={styles.header}>
        <div className={styles.logo}>
          <Image src="/logo.png" alt="Aayudh Logo" className={styles.logoImage} width={40} height={40} style={{ objectFit: 'contain', marginRight: '10px' }} priority />
          <h1>AAYUDH News Assistant</h1>
        </div>
        <div className={styles.userProfile}>
          <button className={styles.syncButton} onClick={handleManualFetch} title="Sync RSS Feeds">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"></path>
              <path d="M3 3v5h5"></path>
              <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"></path>
              <path d="M16 21v-5h5"></path>
            </svg>
            Sync Feeds
          </button>
          <div className={styles.userInfo}>
            <div className={styles.avatar}>E</div>
            <span>Editor</span>
          </div>
        </div>
      </header>

      <div className={styles.container}>
        <div className={styles.controlsContainer}>
          <div className={styles.leftControls}>
            <button 
              className={styles.homeButton} 
              onClick={() => {
                setSearch('');
                setSelectedState('All');
                setSelectedCity('All');
                setSelectedCategory('All');
                setSelectedSource('All');
              }}
              title="Home / Reset Filters"
            >
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
                <polyline points="9 22 9 12 15 12 15 22"></polyline>
              </svg>
            </button>
          </div>
          
          <div className={styles.rightControls}>
            <div className={styles.filterSection}>
              <StateCityFilters 
                states={states}
                cities={cities}
                categories={categories}
                selectedState={selectedState}
                selectedCity={selectedCity}
                selectedCategory={selectedCategory}
                onStateChange={(state) => {
                  setSelectedState(state);
                  if (state !== 'All') {
                    const stateCities = cities[state as keyof typeof cities] || [];
                    if (!stateCities.includes(selectedCity)) {
                      setSelectedCity('All');
                    }
                  }
                }}
                onCityChange={setSelectedCity}
                onCategoryChange={setSelectedCategory}
              />
            </div>
            <div className={styles.searchSection}>
              <SearchBar value={search} onChange={setSearch} onSearch={handleSearch} />
            </div>
          </div>
        </div>

        <div className={styles.layoutWrapper}>
          <aside className={styles.sidebar}>
            <div className={styles.tabsContainer}>
              <button 
                className={`${styles.tab} ${selectedSource === 'All' ? styles.activeTab : ''}`}
                onClick={() => setSelectedSource('All')}
              >
                All Channels
              </button>
              {activeChannels.map(channel => (
                <button 
                  key={channel.id}
                  className={`${styles.tab} ${selectedSource === channel.name ? styles.activeTab : ''}`}
                  onClick={() => setSelectedSource(channel.name)}
                >
                  {channel.name}
                </button>
              ))}
            </div>
          </aside>

          <div className={styles.mainContent}>

        <section className={styles.feedSection}>
          
          {selectedSource === 'All' && (topGridArticles.length > 0 || isLoadingAll) && (
            <div className={styles.topSection}>
              <div className={styles.gridContainer}>
                <div className={styles.feedHeader}>
                  <h2>{selectedSource === 'All' ? 'Latest News' : `${selectedSource} News`}</h2>
                  <span className={styles.resultsCount}>
                    {!isLoadingAll && `${articles.length} results found`}
                  </span>
                </div>
                <NewsFeed 
                  articles={topGridArticles} 
                  isLoading={isLoadingAll} 
                  onGenerateAI={handleGenerateAI}
                  generatingId={generatingId}
                  layout="grid"
                />
                
                {/* Multi-column Latest News grouped by source */}
                {Object.keys(groupedNews).length > 0 && (
                  <div className={styles.multiColumnWrapper}>
                    <h2 className={styles.pramukhSamacharHeading}>प्रमुख समाचार</h2>
                    <div className={styles.multiColumnContainer}>
                      {Object.entries(groupedNews).map(([source, sourceArticles]) => (
                        <div key={source} className={styles.column}>
                          <h3 className={styles.columnHeader}>{source}</h3>
                          <ul className={styles.columnList}>
                            {sourceArticles.slice(0, 5).map(article => (
                              <li key={article.id}>
                                <div className={styles.pramukhContent}>
                                 <span className={styles.arrowIcon}>›</span>
                                 <a href={article.source_url} target="_blank" rel="noopener noreferrer">
                                   {article.title}
                                 </a>
                                </div>
                                <div className={styles.pramukhButtons}>
                                  <button 
                                    onClick={() => handleGenerateAI(article.id)} 
                                    className={styles.pramukhBtn} 
                                    disabled={generatingId === article.id}
                                  >
                                    {generatingId === article.id ? 'Generating...' : 'Generate AI'}
                                  </button>
                                </div>
                              </li>
                            ))}
                          </ul>
                          <button className={styles.viewMoreBtn} onClick={() => setSelectedSource(source)}>
                            {source} से और...
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
              <div 
                className={styles.rightSidebar}
                onMouseEnter={() => { isHoveredRef.current = true; }}
                onMouseLeave={() => { isHoveredRef.current = false; }}
              >
                <div style={{ 
                  display: 'flex',
                  justifyContent: 'center',
                  alignItems: 'center',
                  marginBottom: '1rem', 
                  marginTop: 0, 
                  flexShrink: 0, 
                  backgroundColor: '#6366F1', 
                  padding: '10px', 
                  borderRadius: '6px' 
                }}>
                  <h2 style={{ fontSize: '1.25rem', margin: 0, color: '#FFFFFF', textAlign: 'center' }}>Top News</h2>
                </div>
                <div className={styles.sidebarContent} ref={sidebarRef}>
                  <NewsFeed 
                  articles={articles} 
                  isLoading={isLoadingAll} 
                  onGenerateAI={handleGenerateAI}
                  generatingId={generatingId}
                  layout="sidebar"
                />
                
                {page < totalPages && !isLoadingAll && (
                  <div style={{ display: 'flex', justifyContent: 'center', marginTop: '24px', marginBottom: '24px' }}>
                    <button 
                      onClick={handleLoadMore} 
                      disabled={isLoadingMore}
                      style={{ 
                        padding: '10px 24px', 
                        backgroundColor: 'var(--primary)', 
                        color: 'white', 
                        border: 'none', 
                        borderRadius: '6px',
                        cursor: isLoadingMore ? 'not-allowed' : 'pointer',
                        opacity: isLoadingMore ? 0.7 : 1,
                        width: '100%'
                      }}
                    >
                      {isLoadingMore ? 'Loading...' : 'Load More'}
                    </button>
                  </div>
                )}
                </div>
              </div>
            </div>
          )}

          {selectedSource !== 'All' && (
            <div className={styles.listContainer}>
              <div className={styles.feedHeader}>
                <h2>{selectedSource} News</h2>
                <span className={styles.resultsCount}>
                  {!isLoadingAll && `${articles.length} results found`}
                </span>
              </div>
              <NewsFeed 
                articles={articles} 
                isLoading={isLoadingAll} 
                onGenerateAI={handleGenerateAI}
                generatingId={generatingId}
                layout="grid"
              />
              
              {page < totalPages && !isLoadingAll && (
                <div style={{ display: 'flex', justifyContent: 'center', marginTop: '24px', marginBottom: '24px' }}>
                  <button 
                    onClick={handleLoadMore} 
                    disabled={isLoadingMore}
                    style={{ 
                      padding: '10px 24px', 
                      backgroundColor: 'var(--primary)', 
                      color: 'white', 
                      border: 'none', 
                      borderRadius: '6px',
                      cursor: isLoadingMore ? 'not-allowed' : 'pointer',
                      opacity: isLoadingMore ? 0.7 : 1
                    }}
                  >
                    {isLoadingMore ? 'Loading...' : 'Load More News'}
                  </button>
                </div>
              )}
            </div>
          )}

        </section>
        </div>
      </div>
      </div>

      <AIPanel result={aiResult} onClose={() => setAiResult(null)} />
      {toast && (
        <Toast 
          message={toast.message} 
          type={toast.type} 
          onClose={() => setToast(null)} 
        />
      )}
    </main>
  );
}
