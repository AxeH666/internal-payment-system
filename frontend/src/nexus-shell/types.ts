
import React from 'react';

export type Module = {
  id: string;
  name: string;
  icon: React.ReactNode;
  description: string;
};

export type Site = {
  id: string;
  name: string;
  location: string;
  siteCode?: string;
  clientCode?: string;
};

export interface NavItem {
  label: string;
  icon: React.ReactNode;
  id: string;
  badge?: string | number;
}

export type Role = 'Admin' | 'Creator' | 'Approver' | 'Viewer';

export type ScScope = 'Blockwork' | 'Gypsum' | 'Paints' | 'Electrical' | 'Tilework' | 'GSB Works';
export type VendorType = 'Steel (MS)' | 'Paints' | 'Electrical' | 'Building Material' | 'RMC / Cement' | 'Hardware';

export interface Subcontractor {
  id: string;
  name: string;
  scope: ScScope;
  siteCode: string;
  contactNo: string;
  hasAadhaar: boolean;
  hasPan: boolean;
  hasCheque: boolean;
}

export interface Vendor {
  id: string;
  name: string;
  type: VendorType;
  pocName: string;
  pocContact: string;
  gstin: string;
  hasCheque: boolean;
}

export interface Client {
  id: string;
  name: string;
  location: string;
  clientCode: string;
}
