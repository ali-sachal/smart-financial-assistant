/// <reference types="vite/client" />

declare module 'aws-amplify' {
  export const Amplify: {
    configure: (config: any) => void;
    [key: string]: any;
  };
}

declare module 'aws-amplify/auth' {
  export function fetchAuthSession(options?: any): Promise<{
    tokens?: {
      accessToken?: { toString(): string };
      idToken?: { toString(): string };
    };
    userSub?: string;
    identityId?: string;
  }>;
  export function getCurrentUser(): Promise<{
    username: string;
    userId: string;
    signInDetails?: any;
  }>;
  export function signIn(params: {
    username: string;
    password: string;
    options?: any;
  }): Promise<{
    isSignedIn: boolean;
    nextStep: {
      signInStep: string;
      additionalInfo?: any;
    };
  }>;
  export function signUp(params: {
    username: string;
    password: string;
    options?: any;
  }): Promise<{
    isSignUpComplete: boolean;
    userId?: string;
    nextStep: {
      signUpStep: string;
      codeDeliveryDetails?: any;
    };
  }>;
  export function confirmSignUp(params: {
    username: string;
    confirmationCode: string;
    options?: any;
  }): Promise<{
    isSignUpComplete: boolean;
    nextStep: {
      signUpStep: string;
    };
  }>;
  export function signOut(): Promise<void>;
}

declare module 'lucide-react' {
  import * as React from 'react';
  export interface LucideProps extends React.SVGProps<SVGSVGElement> {
    size?: string | number;
    color?: string;
    strokeWidth?: string | number;
    className?: string;
  }
  export type LucideIcon = React.FC<LucideProps>;

  export const Activity: LucideIcon;
  export const AlertCircle: LucideIcon;
  export const AlertTriangle: LucideIcon;
  export const ArrowDownRight: LucideIcon;
  export const ArrowRight: LucideIcon;
  export const ArrowUpRight: LucideIcon;
  export const Bot: LucideIcon;
  export const Building: LucideIcon;
  export const Calendar: LucideIcon;
  export const CalendarDays: LucideIcon;
  export const Car: LucideIcon;
  export const Check: LucideIcon;
  export const CheckCircle2: LucideIcon;
  export const ChevronDown: LucideIcon;
  export const ChevronRight: LucideIcon;
  export const ChevronUp: LucideIcon;
  export const Cloud: LucideIcon;
  export const Copy: LucideIcon;
  export const CreditCard: LucideIcon;
  export const Database: LucideIcon;
  export const DollarSign: LucideIcon;
  export const Download: LucideIcon;
  export const Eye: LucideIcon;
  export const EyeOff: LucideIcon;
  export const FileCheck: LucideIcon;
  export const FileText: LucideIcon;
  export const Film: LucideIcon;
  export const Fingerprint: LucideIcon;
  export const Flame: LucideIcon;
  export const HeartPulse: LucideIcon;
  export const Image: LucideIcon;
  export const Info: LucideIcon;
  export const KeyRound: LucideIcon;
  export const Layers: LucideIcon;
  export const LayoutDashboard: LucideIcon;
  export const Loader2: LucideIcon;
  export const Lock: LucideIcon;
  export const PieChart: LucideIcon;
  export const PiggyBank: LucideIcon;
  export const Plus: LucideIcon;
  export const Receipt: LucideIcon;
  export const ReceiptText: LucideIcon;
  export const RefreshCw: LucideIcon;
  export const Search: LucideIcon;
  export const Send: LucideIcon;
  export const ShieldAlert: LucideIcon;
  export const ShieldCheck: LucideIcon;
  export const ShoppingCart: LucideIcon;
  export const SlidersHorizontal: LucideIcon;
  export const Sparkles: LucideIcon;
  export const Terminal: LucideIcon;
  export const TrendingUp: LucideIcon;
  export const UploadCloud: LucideIcon;
  export const User: LucideIcon;
  export const Utensils: LucideIcon;
  export const Wrench: LucideIcon;
  export const X: LucideIcon;
  export const Zap: LucideIcon;
}
