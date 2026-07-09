import React from 'react';
import { NewsArticle } from '../types';
import NewsCard from './NewsCard';
import NewsListCard from './NewsListCard';
import CompactNewsCard from './CompactNewsCard';
import styles from './NewsFeed.module.css';

interface NewsFeedProps {
  articles: NewsArticle[];
  isLoading: boolean;
  onGenerateAI: (id: string | number) => void;
  generatingId: string | number | null;
  layout?: 'grid' | 'list' | 'sidebar';
}

export default function NewsFeed({ articles, isLoading, onGenerateAI, generatingId, layout = 'grid' }: NewsFeedProps) {
  if (isLoading) {
    return (
      <div className={styles.loadingContainer}>
        <div className={styles.spinner}></div>
        <p>Loading latest news...</p>
      </div>
    );
  }

  if (articles.length === 0) {
    return (
      <div className={styles.emptyContainer}>
        <h3>No news found</h3>
        <p>Try adjusting your search keywords or filters.</p>
      </div>
    );
  }

  return (
    <div className={layout === 'grid' ? styles.grid : styles.list}>
      {articles.map((article) => {
        if (layout === 'grid') {
          return (
            <NewsCard 
              key={article.id} 
              article={article} 
              onGenerateAI={onGenerateAI}
              isGenerating={generatingId === article.id}
            />
          );
        } else if (layout === 'sidebar') {
          return (
            <CompactNewsCard 
              key={article.id} 
              article={article} 
            />
          );
        } else {
          return (
            <NewsListCard
              key={article.id} 
              article={article} 
              onGenerateAI={onGenerateAI}
              isGenerating={generatingId === article.id}
            />
          );
        }
      })}
    </div>
  );
}
