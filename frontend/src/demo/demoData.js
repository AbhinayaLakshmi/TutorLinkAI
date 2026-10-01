/**
 * TutorLinkAI - Academic Project Review Demo Data
 * 
 * Controlled synthetic benchmark data for demonstrating:
 * 1. Learning-Need Specific Matching
 * 2. Semantic & Topic Overlap Compatibility
 * 3. Multi-Criteria Ranking (Learning Need, Location, Fee, Time)
 * 4. Evidence-Grounded Explainability ("Why This Tutor?")
 * 5. Counterfactual Recommendation ("What Would Change Your Recommendation?")
 * 
 * DISCLAIMER:
 * DEMO MODE ONLY. Uses controlled synthetic data for project evaluation.
 * Does not represent live users or genuine identity verifications.
 */

export const DEMO_STUDENT_NEED = {
  id: "need-rotational-dynamics",
  title: "Physics – Rotational Dynamics Preparation",
  student_name: "Alex Kumar",
  student_level: "Undergraduate",
  course: "B.Sc. Physics (2nd Year)",
  subject: "Physics",
  topics: ["Rotational Dynamics", "Classical Mechanics"],
  learning_goal: "Understand difficult rotational dynamics concepts (moment of inertia, torque, angular momentum conservation, rigid body motion) and prepare for university examinations",
  preferred_learning_mode: "Online",
  preferred_language: "English",
  maximum_budget: 700, // ₹700/hour
  preferred_skills: ["Concept Teaching", "Problem Solving", "Exam Preparation"],
  location: "Online / Remote",
  availability: "Weekdays & Weekends (Flexible Evening)",
};

/**
 * Raw candidate pool (5 synthetic candidates)
 */
export const RAW_DEMO_TUTORS = [
  {
    id: "tutor-c",
    name: "Dr. A. Ramanathan (Demo C)",
    avatar: "👨‍🏫",
    initials: "AR",
    title: "Ph.D. in Physics • Undergraduate Specialist",
    bio: "Specialized in classical mechanics, angular kinematics, rotational dynamics, and university exam preparation with 8+ years of university tutoring experience.",
    subjects: ["Physics"],
    topics: ["Classical Mechanics", "Rotational Dynamics", "Exam Preparation"],
    skills: ["Exam Preparation", "Problem Solving", "Concept Teaching"],
    student_levels: ["Undergraduate"],
    languages: ["English", "Tamil"],
    teaching_mode: "Online",
    hourly_rate: 650,
    rating: 4.95,
    total_reviews: 42,
    semantic_score: 0.96,
    topic_score: 1.00,
    matched_topics: ["Rotational Dynamics", "Classical Mechanics"],
    unmatched_topics: ["Exam Preparation"],
    location_score: 1.00,
    time_score: 0.95,
    match_reasons: [
      "Strong topic alignment: Rotational Dynamics & Classical Mechanics",
      "Matches undergraduate student level",
      "Supports dedicated examination preparation",
      "Online teaching available",
      "Within your budget (₹650/hr ≤ ₹700/hr)",
      "Strong semantic alignment with your exam-oriented learning goal"
    ],
    explanation_summary:
      "Recommended because this tutor has strong alignment with your learning need, particularly Rotational Dynamics and Classical Mechanics, and supports undergraduate exam preparation.",
    badge: "⭐ TOP RECOMMENDATION"
  },
  {
    id: "tutor-a",
    name: "Prof. Rajesh Sharma (Demo A)",
    avatar: "👨‍🔬",
    initials: "RS",
    title: "M.Sc. Physics • Classical Mechanics Expert",
    bio: "6+ years teaching mechanics and rotational dynamics to undergraduate and high school students with step-by-step problem solving methodology.",
    subjects: ["Physics"],
    topics: ["Rotational Dynamics", "Classical Mechanics", "Mechanics"],
    skills: ["Concept Teaching", "Exam Preparation", "Problem Solving"],
    student_levels: ["Undergraduate", "High School"],
    languages: ["English"],
    teaching_mode: "Online",
    hourly_rate: 500,
    rating: 4.85,
    total_reviews: 38,
    semantic_score: 0.90,
    topic_score: 0.95,
    matched_topics: ["Rotational Dynamics", "Classical Mechanics"],
    unmatched_topics: ["Mechanics"],
    location_score: 1.00,
    time_score: 0.90,
    match_reasons: [
      "Strong topic alignment: Rotational Dynamics & Mechanics",
      "Matches undergraduate level",
      "Supports exam preparation & problem solving",
      "Online teaching available",
      "Cost-effective hourly rate (₹500/hr ≤ ₹700/hr)",
      "Strong semantic alignment with learning goal"
    ],
    explanation_summary:
      "Strong candidate with comprehensive coverage of rotational dynamics and classical mechanics, well within student budget.",
    badge: "💰 HIGH AFFORDABILITY MATCH"
  },
  {
    id: "tutor-d",
    name: "Kavitha Sundaram (Demo D)",
    avatar: "👩‍🏫",
    initials: "KS",
    title: "M.Sc. Applied Physics • Optics Tutor",
    bio: "4 years tutoring college physics with an emphasis on optics, ray matrices, and electromagnetism concepts.",
    subjects: ["Physics"],
    topics: ["Optics", "Electromagnetism"],
    skills: ["Concept Teaching"],
    student_levels: ["Undergraduate"],
    languages: ["English"],
    teaching_mode: "Online",
    hourly_rate: 400,
    rating: 4.60,
    total_reviews: 19,
    semantic_score: 0.58,
    topic_score: 0.00,
    matched_topics: [],
    unmatched_topics: ["Optics", "Electromagnetism"],
    location_score: 1.00,
    time_score: 0.90,
    match_reasons: [
      "General physics subject match",
      "Matches undergraduate level",
      "Highly affordable hourly rate (₹400/hr)",
      "Online teaching mode available"
    ],
    explanation_summary:
      "Affordable physics tutor, but primary teaching focus is Optics and Electromagnetism rather than Rotational Dynamics.",
    badge: "MODERATE MATCH"
  },
  {
    id: "tutor-b",
    name: "Siddharth Verma (Demo B)",
    avatar: "👨‍🎓",
    initials: "SV",
    title: "M.Tech Engineering • Thermodynamics Specialist",
    bio: "5 years teaching thermal physics, fluid dynamics, and waves with focus on numerical calculations.",
    subjects: ["Physics"],
    topics: ["Thermodynamics", "Waves", "Heat"],
    skills: ["Concept Teaching", "Numerical Problem Solving"],
    student_levels: ["Undergraduate"],
    languages: ["English"],
    teaching_mode: "Online",
    hourly_rate: 450,
    rating: 4.55,
    total_reviews: 24,
    semantic_score: 0.52,
    topic_score: 0.00,
    matched_topics: [],
    unmatched_topics: ["Thermodynamics", "Waves", "Heat"],
    location_score: 1.00,
    time_score: 0.85,
    match_reasons: [
      "General physics subject match",
      "Matches undergraduate level",
      "Online teaching available",
      "Within budget (₹450/hr)"
    ],
    explanation_summary:
      "Subject matches physics, but specializes in Thermodynamics and Waves rather than Rotational Dynamics.",
    badge: "LOW TOPIC ALIGNMENT"
  },
  {
    id: "tutor-math",
    name: "Ananya Iyer (Demo Math)",
    avatar: "👩‍🔬",
    initials: "AI",
    title: "M.Sc. Mathematics • Calculus & Differential Equations",
    bio: "7 years teaching undergraduate mathematics, multivariable calculus, and differential equations for engineering students.",
    subjects: ["Mathematics"],
    topics: ["Calculus", "Integration", "Differential Equations"],
    skills: ["Concept Teaching", "Exam Preparation"],
    student_levels: ["Undergraduate"],
    languages: ["English"],
    teaching_mode: "Online",
    hourly_rate: 600,
    rating: 4.70,
    total_reviews: 31,
    semantic_score: 0.20,
    topic_score: 0.00,
    matched_topics: [],
    unmatched_topics: ["Calculus", "Integration", "Differential Equations"],
    location_score: 1.00,
    time_score: 0.80,
    match_reasons: [
      "Undergraduate university level support",
      "Online teaching available",
      "Concept teaching pedagogy"
    ],
    explanation_summary:
      "Subject mismatch (Mathematics instead of Physics), though offers foundational mathematical and calculus tools.",
    badge: "SUBJECT MISMATCH"
  }
];

/**
 * Multi-criteria ranking and dynamic score computation
 * Formula:
 * learning_need = 0.50 * semantic + 0.50 * topic
 * overall = 0.45 * learning_need + 0.20 * location + 0.20 * fee + 0.15 * time
 */
export function computeTutorScores(tutor, currentBudget = 700) {
  // Learning need composite score
  const learning_need_score = 0.50 * tutor.semantic_score + 0.50 * tutor.topic_score;
  
  // Fee score dynamically evaluated against current student budget
  let fee_score = 1.0;
  if (tutor.hourly_rate <= currentBudget) {
    // Within budget: slight preference to lower rates or high efficiency
    // normalized between 0.90 and 1.0
    const ratio = tutor.hourly_rate / currentBudget;
    fee_score = Math.max(0.85, 1.0 - 0.12 * ratio);
  } else {
    // Over budget: penalty decays rapidly
    const overage = (tutor.hourly_rate - currentBudget) / currentBudget;
    fee_score = Math.max(0.10, 1.0 - 2.8 * overage);
  }

  // Multi-criteria overall score calculation
  const overall_score =
    0.45 * learning_need_score +
    0.20 * tutor.location_score +
    0.20 * fee_score +
    0.15 * tutor.time_score;

  const overall_percentage = Math.round(overall_score * 100);
  const learning_need_percentage = Math.round(learning_need_score * 100);
  const topic_percentage = Math.round(tutor.topic_score * 100);
  const fee_percentage = Math.round(fee_score * 100);
  const time_percentage = Math.round(tutor.time_score * 100);
  const location_percentage = Math.round(tutor.location_score * 100);

  return {
    ...tutor,
    current_fee_score: fee_score,
    learning_need_score,
    overall_score,
    overall_percentage,
    breakdown: {
      learning_need_score,
      learning_need_percentage,
      semantic_score: tutor.semantic_score,
      semantic_percentage: Math.round(tutor.semantic_score * 100),
      topic_score: tutor.topic_score,
      topic_percentage,
      fee_score,
      fee_percentage,
      time_score: tutor.time_score,
      time_percentage,
      location_score: tutor.location_score,
      location_percentage,
      overall_percentage
    }
  };
}

/**
 * Returns all tutors scored and sorted by overall_score descending for a given budget
 */
export function getRankedDemoTutors(budget = 700) {
  return RAW_DEMO_TUTORS
    .map((t) => computeTutorScores(t, budget))
    .sort((a, b) => b.overall_score - a.overall_score);
}
