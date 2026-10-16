"""
Synthetic aviation incident/accident report generator.

The synopsis calls for a collection of publicly available aviation reports. Real
datasets (NTSB, ASRS) can be plugged in via ``data_loader.py``; this generator
produces a realistic, self-contained corpus so the full pipeline (embeddings,
topic modelling, clustering, trend/relationship analysis, semantic search) always
runs and yields *meaningful* results even with no internet access.

Design goals
------------
* Each narrative is written in aviation-report style natural language.
* The same underlying contributing factor is expressed with different words
  (e.g. "poor visibility" / "reduced visibility" / "fog on approach") so that
  semantic embeddings clearly outperform keyword matching.
* Factors deliberately co-occur (weather + loss-of-control, maintenance +
  engine, fatigue + communication) so relationship analysis finds real edges.
* Some factors trend up or down across the years so trend analysis is non-trivial.
* Output is fully deterministic given the seed, so analyses are reproducible.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

import pandas as pd

# --------------------------------------------------------------------------- #
# Vocabulary pools
# --------------------------------------------------------------------------- #

AIRCRAFT = [
    "Cessna 172", "Cessna 208 Caravan", "Piper PA-28 Cherokee", "Beechcraft Bonanza",
    "Boeing 737-800", "Airbus A320", "Embraer E175", "Bombardier CRJ-900",
    "Boeing 777-300ER", "Airbus A321neo", "ATR 72", "Diamond DA40",
    "Cirrus SR22", "Robinson R44", "Gulfstream G550", "Boeing 787-9",
]

AIRPORTS = [
    ("KJFK", "New York, NY"), ("KLAX", "Los Angeles, CA"), ("KORD", "Chicago, IL"),
    ("KDEN", "Denver, CO"), ("KSFO", "San Francisco, CA"), ("KATL", "Atlanta, GA"),
    ("KSEA", "Seattle, WA"), ("KBOS", "Boston, MA"), ("KMIA", "Miami, FL"),
    ("KASE", "Aspen, CO"), ("KTEB", "Teterboro, NJ"), ("KAPA", "Denver-Centennial, CO"),
    ("KPWK", "Chicago-Executive, IL"), ("KSNA", "Santa Ana, CA"), ("KHPN", "White Plains, NY"),
    ("KBFI", "Seattle-Boeing Field, WA"), ("KFLL", "Fort Lauderdale, FL"),
    ("KDVT", "Phoenix-Deer Valley, AZ"), ("KJAC", "Jackson Hole, WY"), ("KEGE", "Eagle, CO"),
]

OPERATORS = [
    "a regional air carrier", "a major airline", "a private owner",
    "a charter operator", "a flight training school", "a corporate flight department",
    "a cargo operator", "an air ambulance operator",
]

# --------------------------------------------------------------------------- #
# Contributing-factor definitions.
# Each factor has:
#   phases     : plausible phases of flight
#   openers    : sentence describing the triggering condition (synonym variants)
#   effects    : the consequence / how it developed
#   companions : factors that plausibly co-occur (id -> weight)
# --------------------------------------------------------------------------- #


@dataclass
class Factor:
    fid: str
    label: str
    phases: List[str]
    openers: List[str]
    effects: List[str]
    companions: Dict[str, float] = field(default_factory=dict)
    # year_trend maps to a multiplier applied per year offset (0..n) to bias the
    # temporal distribution. Positive slope => more common in later years.
    slope: float = 0.0


FACTORS: List[Factor] = [
    Factor(
        "weather_vis", "Weather & Low Visibility",
        ["approach", "landing", "takeoff", "cruise"],
        [
            "The flight encountered poor visibility with fog reported along the approach path.",
            "Reduced visibility and low ceilings were present in the terminal area at the time.",
            "Dense fog rolled across the field, cutting forward visibility to well below minimums.",
            "The crew reported deteriorating visibility and mist obscuring the runway environment.",
            "Marginal visual conditions and a lowering cloud base were noted during the descent.",
        ],
        [
            "The crew initiated a missed approach after losing sight of the runway.",
            "The pilot continued below the decision height and the aircraft touched down long.",
            "Spatial awareness was degraded and the flight deviated from the published track.",
            "A go-around was flown and the aircraft diverted to the alternate airport.",
        ],
        {"loss_of_control": 0.35, "cfit_nav": 0.25, "comm_atc": 0.15},
        slope=-0.4,
    ),
    Factor(
        "icing", "Airframe & Carburettor Icing",
        ["climb", "cruise", "approach"],
        [
            "Airframe ice accumulated rapidly after the aircraft entered a band of freezing precipitation.",
            "The pilot observed carburettor icing symptoms with a gradual loss of engine RPM.",
            "Structural icing built up on the leading edges while operating in visible moisture near freezing.",
            "Ice accretion on the wings and tail degraded the aircraft's performance.",
        ],
        [
            "The aircraft became difficult to control as the stall speed increased.",
            "Engine power decayed and the pilot applied carburettor heat to recover.",
            "The crew requested a lower altitude to exit the icing layer.",
            "Climb performance deteriorated and the flight was unable to maintain altitude.",
        ],
        {"loss_of_control": 0.4, "engine_power": 0.3, "weather_vis": 0.2},
        slope=0.1,
    ),
    Factor(
        "wind_crosswind", "Wind & Crosswind",
        ["landing", "takeoff"],
        [
            "A gusty crosswind exceeding the demonstrated limit was present during the landing roll.",
            "Strong and variable surface winds produced significant wind shear on short final.",
            "The aircraft encountered a sudden gust and drifted from the runway centreline.",
            "Wind shear on approach caused a rapid loss of airspeed close to the ground.",
        ],
        [
            "The aircraft touched down hard and departed the side of the runway.",
            "A wing dropped during the flare and the wingtip contacted the surface.",
            "The pilot lost directional control and the aircraft ground-looped.",
            "The landing was aborted and a go-around was initiated.",
        ],
        {"runway_excursion": 0.5, "loss_of_control": 0.3},
        slope=0.0,
    ),
    Factor(
        "engine_power", "Engine & Powerplant Failure",
        ["takeoff", "climb", "cruise"],
        [
            "The engine experienced a partial loss of power shortly after rotation.",
            "A complete engine failure occurred during the initial climb.",
            "The crew noted fluctuating oil pressure followed by a power loss.",
            "Abnormal engine vibration preceded a significant reduction in thrust.",
            "One engine surged and then rolled back to idle without commanded input.",
        ],
        [
            "The pilot executed a forced landing in a field beyond the airport boundary.",
            "The crew declared an emergency and returned to the departure airport.",
            "The aircraft was unable to maintain altitude and descended into terrain.",
            "A precautionary shutdown was carried out and a single-engine approach was flown.",
        ],
        {"maintenance": 0.5, "fuel": 0.25, "forced_landing": 0.3},
        slope=-0.1,
    ),
    Factor(
        "fuel", "Fuel Exhaustion & Management",
        ["cruise", "approach", "descent"],
        [
            "The aircraft ran out of usable fuel before reaching the destination.",
            "Fuel starvation occurred after the crew failed to switch tanks in time.",
            "The flight was dispatched with insufficient fuel reserves for the conditions.",
            "Water contamination was later found in the fuel samples.",
            "Fuel mismanagement led to an unexpected engine stoppage in cruise.",
        ],
        [
            "Both engines lost power and the crew glided to an off-airport landing.",
            "The pilot made an emergency landing on a highway short of the runway.",
            "The aircraft touched down in a field with the engine windmilling.",
        ],
        {"engine_power": 0.4, "human_factors": 0.35, "forced_landing": 0.3},
        slope=-0.2,
    ),
    Factor(
        "landing_gear", "Landing Gear Malfunction",
        ["landing", "approach"],
        [
            "The landing gear failed to extend and lock down on approach.",
            "A gear-up landing was carried out after the extension system malfunctioned.",
            "The nose gear collapsed during the landing rollout.",
            "The crew received an unsafe gear indication and ran the emergency checklist.",
        ],
        [
            "The aircraft slid down the runway on its belly with minor structural damage.",
            "The propeller and lower fuselage were substantially damaged.",
            "The aircraft came to rest on the runway and was later recovered.",
        ],
        {"maintenance": 0.45, "runway_excursion": 0.2},
        slope=0.0,
    ),
    Factor(
        "runway_excursion", "Runway Excursion & Overrun",
        ["landing", "takeoff"],
        [
            "The aircraft overran the end of the runway during the landing rollout.",
            "A runway excursion occurred when the aircraft departed the paved surface.",
            "The aircraft failed to stop within the available runway distance.",
            "A contaminated, wet runway reduced braking effectiveness significantly.",
        ],
        [
            "The aircraft came to rest in the grass beyond the runway threshold.",
            "The nose gear dug into soft ground and the aircraft sustained damage.",
            "No injuries were reported but the runway was closed for recovery.",
        ],
        {"wind_crosswind": 0.3, "weather_vis": 0.25, "brakes_hydraulics": 0.3},
        slope=0.1,
    ),
    Factor(
        "bird_strike", "Bird & Wildlife Strike",
        ["takeoff", "climb", "approach"],
        [
            "The aircraft struck a flock of birds shortly after takeoff.",
            "A large bird was ingested into the number two engine during the climb.",
            "Wildlife on the runway was encountered during the landing roll.",
            "Multiple bird strikes were reported on the windshield and leading edges.",
        ],
        [
            "The crew returned for a precautionary landing and inspection.",
            "Engine vibration prompted a precautionary shutdown.",
            "Damage was found on the radome and one engine cowling.",
        ],
        {"engine_power": 0.4},
        slope=0.25,
    ),
    Factor(
        "human_factors", "Human Factors & Fatigue",
        ["cruise", "approach", "descent", "landing"],
        [
            "The crew was operating on the final leg of a long duty day and reported fatigue.",
            "A lapse in attention and high workload contributed to a missed checklist item.",
            "The pilot became distracted during a critical phase of flight.",
            "Crew fatigue and time pressure degraded decision making on the approach.",
            "Complacency and a break in the normal routine led to an error being missed.",
        ],
        [
            "A configuration error was not caught before landing.",
            "The crew descended below the assigned altitude without noticing.",
            "An incorrect runway was briefly selected before the error was corrected.",
        ],
        {"comm_atc": 0.4, "fuel": 0.2, "weather_vis": 0.2},
        slope=0.35,
    ),
    Factor(
        "comm_atc", "Communication & ATC Coordination",
        ["taxi", "takeoff", "approach", "cruise"],
        [
            "A readback error led the crew to accept an incorrect altitude clearance.",
            "Miscommunication with air traffic control resulted in a runway confusion event.",
            "A blocked radio transmission caused the crew to miss an instruction.",
            "The controller and crew had a misunderstanding about the assigned taxi route.",
            "Frequency congestion delayed a critical clearance during a busy period.",
        ],
        [
            "The aircraft entered an active runway without a proper clearance.",
            "A loss of separation with another aircraft was reported.",
            "The crew initiated a go-around after the confusion was identified.",
        ],
        {"human_factors": 0.4, "runway_incursion": 0.5},
        slope=0.2,
    ),
    Factor(
        "runway_incursion", "Runway Incursion",
        ["taxi", "takeoff"],
        [
            "The aircraft crossed the hold-short line without clearance onto an active runway.",
            "A vehicle entered the runway while an aircraft was on short final.",
            "Two aircraft were on the same runway due to a coordination breakdown.",
            "The crew took a wrong turn on the taxiway and approached an active runway.",
        ],
        [
            "The departing aircraft rejected the takeoff to avoid a conflict.",
            "Controllers issued an immediate go-around to the landing traffic.",
            "Separation was maintained but the event was classified as a serious incursion.",
        ],
        {"comm_atc": 0.55, "human_factors": 0.3},
        slope=0.15,
    ),
    Factor(
        "maintenance", "Maintenance & Component Wear",
        ["cruise", "climb", "approach", "takeoff"],
        [
            "A component failed due to improper maintenance carried out at the last inspection.",
            "Excessive wear on a critical part was not detected during scheduled maintenance.",
            "An incorrectly installed part came loose during flight.",
            "Corrosion and fatigue cracking were later found in the failed component.",
            "A maintenance error left a control system out of adjustment.",
        ],
        [
            "The defect led to a system failure that required an emergency return.",
            "The crew managed the failure using the abnormal procedures checklist.",
            "The part separated in flight and caused secondary damage.",
        ],
        {"engine_power": 0.4, "landing_gear": 0.25, "brakes_hydraulics": 0.3},
        slope=-0.15,
    ),
    Factor(
        "brakes_hydraulics", "Brakes & Hydraulic System",
        ["landing", "taxi", "approach"],
        [
            "A hydraulic system failure left the crew with degraded braking.",
            "Brake fade during the landing roll reduced deceleration.",
            "A hydraulic leak led to a loss of nosewheel steering.",
            "The anti-skid system malfunctioned on a wet runway.",
        ],
        [
            "The aircraft was unable to stop on the remaining runway.",
            "The crew used the emergency brake accumulator to stop the aircraft.",
            "Directional control was difficult during the rollout.",
        ],
        {"runway_excursion": 0.45, "maintenance": 0.35},
        slope=0.0,
    ),
    Factor(
        "loss_of_control", "Loss of Control In-Flight",
        ["climb", "cruise", "approach", "manoeuvring"],
        [
            "The aircraft entered an aerodynamic stall from which recovery was delayed.",
            "The pilot experienced spatial disorientation in instrument conditions.",
            "An uncommanded roll developed and the aircraft departed controlled flight.",
            "The aircraft was allowed to slow below a safe speed during a steep turn.",
        ],
        [
            "The aircraft entered a spin and impacted terrain.",
            "The pilot recovered at low altitude with substantial altitude loss.",
            "Control was regained after the autopilot was disconnected.",
        ],
        {"weather_vis": 0.3, "icing": 0.25, "human_factors": 0.3},
        slope=-0.1,
    ),
    Factor(
        "cfit_nav", "Navigation & Terrain Awareness",
        ["approach", "descent", "cruise"],
        [
            "A navigation error placed the aircraft off the intended course toward high terrain.",
            "The crew descended below the minimum safe altitude in mountainous terrain.",
            "A GPS database error routed the flight toward rising ground.",
            "The terrain awareness warning system activated during a night approach.",
        ],
        [
            "The crew executed an escape manoeuvre and climbed clear of terrain.",
            "The aircraft came within a few hundred feet of the ground before recovery.",
            "A controlled flight into terrain event was narrowly avoided.",
        ],
        {"weather_vis": 0.4, "human_factors": 0.3},
        slope=-0.05,
    ),
    Factor(
        "forced_landing", "Forced / Emergency Landing",
        ["cruise", "descent", "approach"],
        [
            "Following an in-flight emergency the crew set up for an off-airport landing.",
            "A precautionary landing was made in an open field.",
            "The pilot selected an emergency landing site after the malfunction.",
        ],
        [
            "The aircraft was substantially damaged but the occupants escaped injury.",
            "The touchdown was firm and the aircraft nosed over in soft terrain.",
            "The landing was successful and there were no injuries.",
        ],
        {"engine_power": 0.5, "fuel": 0.35},
        slope=0.0,
    ),
]

FACTOR_BY_ID = {f.fid: f for f in FACTORS}

SEVERITY = ["Incident", "Serious Incident", "Accident"]
INJURY = ["None", "Minor", "Serious", "Fatal"]


def _weighted_choice(rng: random.Random, items: List, weights: List[float]):
    return rng.choices(items, weights=weights, k=1)[0]


def _pick_companion(rng: random.Random, factor: Factor) -> Optional[Factor]:
    """Return a co-occurring factor, or None."""
    for cid, prob in factor.companions.items():
        if rng.random() < prob:
            comp = FACTOR_BY_ID.get(cid)
            if comp and comp.fid != factor.fid:
                return comp
    return None


def _year_weights(years: List[int], factor: Factor) -> List[float]:
    n = len(years)
    base = 1.0
    return [max(0.05, base + factor.slope * (i - n / 2) / max(1, n / 2)) for i in range(n)]


def generate_reports(n: int = 480, seed: int = 42,
                     start_year: int = 2015, end_year: int = 2024) -> pd.DataFrame:
    """Generate ``n`` synthetic aviation reports as a DataFrame."""
    rng = random.Random(seed)
    years = list(range(start_year, end_year + 1))

    rows = []
    # Roughly balance the primary factor distribution but keep it uneven so that
    # some topics are clearly larger than others.
    factor_weights = [1.0 + 0.5 * ((i * 7) % 5) / 5 for i in range(len(FACTORS))]

    for k in range(n):
        primary = _weighted_choice(rng, FACTORS, factor_weights)
        yr = _weighted_choice(rng, years, _year_weights(years, primary))
        month = rng.randint(1, 12)
        day = rng.randint(1, 28)
        d = date(yr, month, day)

        phase = rng.choice(primary.phases)
        aircraft = rng.choice(AIRCRAFT)
        icao, place = rng.choice(AIRPORTS)
        operator = rng.choice(OPERATORS)

        companion = _pick_companion(rng, primary)

        # The *event text* describes only what happened (the contributing
        # factors and their effects).  This is what the NLP pipeline embeds and
        # topic-models, so that topics reflect factors rather than aircraft type.
        body_parts = [rng.choice(primary.openers)]
        if companion is not None:
            body_parts.append(rng.choice(companion.openers))
        body_parts.append(rng.choice(primary.effects))
        if companion is not None and rng.random() < 0.6:
            body_parts.append(rng.choice(companion.effects))
        event_text = " ".join(body_parts)

        # The full narrative additionally carries the structured context
        # (aircraft, location, operator) once, the way a real report reads.
        # NER and the UI use this richer form.
        lead = (
            f"During the {phase} phase of flight, a {aircraft} operating near "
            f"{place} ({icao}) on behalf of {operator} was involved in the occurrence."
        )
        narrative = lead + " " + event_text

        severity = _weighted_choice(rng, SEVERITY, [0.55, 0.3, 0.15])
        if severity == "Accident":
            injury = _weighted_choice(rng, INJURY, [0.4, 0.3, 0.2, 0.1])
        elif severity == "Serious Incident":
            injury = _weighted_choice(rng, INJURY, [0.7, 0.25, 0.05, 0.0])
        else:
            injury = _weighted_choice(rng, INJURY, [0.9, 0.1, 0.0, 0.0])

        # Ground-truth factor labels are stored only for evaluation / colouring;
        # the unsupervised pipeline never reads them.
        truth = [primary.label] + ([companion.label] if companion else [])

        rows.append({
            "report_id": f"AV-{start_year}-{k:04d}",
            "date": d.isoformat(),
            "narrative": narrative,
            "event_text": event_text,
            "aircraft_type": aircraft,
            "airport": icao,
            "location": place,
            "operator": operator.replace("a ", "").replace("an ", "").title(),
            "phase_of_flight": phase,
            "severity": severity,
            "injury_level": injury,
            "true_factors": "; ".join(truth),   # reference only
        })

    df = pd.DataFrame(rows)
    df = df.sort_values("date").reset_index(drop=True)
    return df


if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser(description="Generate the synthetic aviation dataset.")
    parser.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "reports.csv"))
    parser.add_argument("--n", type=int, default=480)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    frame = generate_reports(n=args.n, seed=args.seed)
    frame.to_csv(args.out, index=False)
    print(f"Wrote {len(frame)} reports to {args.out}")
    print(frame[["report_id", "date", "severity"]].head())
