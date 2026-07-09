import React from 'react';
import styles from './StateCityFilters.module.css';

interface StateCityFiltersProps {
  states: string[];
  cities: Record<string, string[]>;
  categories: string[];
  selectedState: string;
  selectedCity: string;
  selectedCategory: string;
  onStateChange: (state: string) => void;
  onCityChange: (city: string) => void;
  onCategoryChange: (category: string) => void;
}

export default function StateCityFilters({ 
  states, 
  cities, 
  categories,
  selectedState, 
  selectedCity, 
  selectedCategory,
  onStateChange, 
  onCityChange,
  onCategoryChange
}: StateCityFiltersProps) {
  
  const currentCities = cities[selectedState] || cities['All'] || [];

  return (
    <div className={styles.container}>
      <div className={styles.filterGroup}>
        <label className={styles.label}>Category</label>
        <div className={styles.selectWrapper}>
          <select 
            className={styles.select} 
            value={selectedCategory}
            onChange={(e) => onCategoryChange(e.target.value)}
          >
            {categories.map(c => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
          <div className={styles.icon}>▼</div>
        </div>
      </div>
      
      <div className={styles.filterGroup}>
        <label className={styles.label}>State</label>
        <div className={styles.selectWrapper}>
          <select 
            className={styles.select} 
            value={selectedState}
            onChange={(e) => onStateChange(e.target.value)}
          >
            {states.map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
          <div className={styles.icon}>▼</div>
        </div>
      </div>
      
      <div className={styles.filterGroup}>
        <label className={styles.label}>City</label>
        <div className={styles.selectWrapper}>
          <select 
            className={styles.select} 
            value={selectedCity}
            onChange={(e) => onCityChange(e.target.value)}
            disabled={!currentCities.length}
          >
            {currentCities.map(c => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
          <div className={styles.icon}>▼</div>
        </div>
      </div>
    </div>
  );
}
