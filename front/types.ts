export type PinShape = 'pin' | 'circle' | 'star' | 'square' | 'triangle';

export interface LatLng {
  lat: number;
  lng: number;
}

export interface Pin {
  id: string;
  name: string;
  position: LatLng;
  color: string;
  shape: PinShape;
  description?: string;
}

export interface MapCircle {
  id: string;
  center: LatLng;
  radius: number; // in meters
  color: string;
}

export interface RulerState {
  isActive: boolean;
  points: LatLng[];
  distance: number | null; // in meters
}

export interface AIResponse {
  lat: number;
  lng: number;
  suggestedName: string;
  suggestedColor: string;
  suggestedShape: PinShape;
  description: string;
}

export interface CellTowerMarker {
  id: number | string;
  radio_type: string;
  mcc: number;
  mnc: number;
  lac: number | null;
  cell_id: number | null;
  pci: number | null;
  earfcn: number | null;
  lat: number;
  lon: number;
  tx_power: number | null;
  source: string;
}

export interface SnapshotPhoneLocation {
  lat: number;
  lng: number;
  accuracy?: number | null;
  type?: string | null;
  timestamp?: string | null;
}

export interface LocateComputed {
  location: { lat: number; lon: number; google: string };
  radius: number;
  debug: {
    source: string;
    bearing_used: number | null;
    signal: number | null;
    confidence?: string | null;
  };
}

export interface SnapshotLocateResponse {
  snapshot_id: number;
  phone_location: SnapshotPhoneLocation | null;
  computed: LocateComputed;
  extracted_cells_count: number;
  snapshot_cells?: Array<{
    idx?: number | null;
    type?: string | null;
    registered?: boolean | null;
    mcc?: number | null;
    mnc?: number | null;
    lac?: number | null;
    cell_id?: number | null;
    pci?: number | null;
    earfcn?: number | null;
    rsrp?: number | null;
    rsrq?: number | null;
    dbm?: number | null;
    alphaLong?: string | null;
    alphaShort?: string | null;
    bandwidth?: number | null;
    level?: number | null;
    tower_found?: boolean;
    tower_lat?: number | null;
    tower_lon?: number | null;
    tower_source?: string | null;
  }>;
  cells?: Array<{
    radio_type?: string | null;
    mcc?: number | null;
    mnc?: number | null;
    lac?: number | null;
    cell_id?: number | null;
    pci?: number | null;
    earfcn?: number | null;
    signalStrength?: number | null;
    timingAdvance?: number | null;
    registered?: boolean | null;
    tower_found?: boolean;
    tower_lat?: number | null;
    tower_lon?: number | null;
    tower_source?: string | null;
  }>;
  anchors?: Array<
    CellTowerMarker & {
      rsrp?: number | null;
    }
  >;
}
