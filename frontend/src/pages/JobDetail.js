import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import { API } from '@/App';
import { Briefcase, MapPin, Clock, DollarSign, CheckCircle, ArrowLeft, Loader2, LogOut } from 'lucide-react';

const JobDetail = ({ user, onLogout }) => {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [applying, setApplying] = useState(false);
  const [hasApplied, setHasApplied] = useState(false);

  useEffect(() => {
  fetchJobDetails();
  if (user.role === 'job_seeker') {
    checkApplicationStatus();
  }
}, [jobId, user.role, fetchJobDetails, checkApplicationStatus]);

  const fetchJobDetails = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API}/jobs/${jobId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.ok) {
        setJob(await response.json());
      } else {
        toast.error('Job not found');
        navigate('/jobs');
      }
    } catch (error) {
      toast.error('Error loading job details');
    } finally {
      setLoading(false);
    }
  }, [jobId]);

  const checkApplicationStatus = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API}/applications`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.ok) {
        const applications = await response.json();
        const applied = applications.some(app => app.job_id === jobId);
        setHasApplied(applied);
      }
    } catch (error) {
      console.error('Error checking application status');
    }
  }, [jobId, user.role]);

  const handleApply = async () => {
    setApplying(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API}/applications`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ job_id: jobId })
      });

      if (response.ok) {
        toast.success('Application submitted successfully!');
        setHasApplied(true);
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to apply');
      }
    } catch (error) {
      toast.error('Network error. Please try again.');
    } finally {
      setApplying(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  if (!job) return null;

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-emerald-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-md border-b border-slate-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <Link to="/" className="flex items-center gap-2">
              <Briefcase className="w-8 h-8 text-indigo-600" />
              <span className="text-2xl font-bold" style={{ fontFamily: 'Outfit' }}>ResuMatch</span>
            </Link>
            <div className="flex items-center gap-4">
              <Link to={user.role === 'job_seeker' ? '/dashboard' : '/employer'}>
                <Button data-testid="dashboard-link-btn" variant="ghost" className="rounded-full">Dashboard</Button>
              </Link>
              <Button data-testid="logout-btn" onClick={onLogout} variant="outline" className="rounded-full" size="sm">
                <LogOut className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Button data-testid="back-btn" onClick={() => navigate(-1)} variant="ghost" className="mb-6 rounded-full">
          <ArrowLeft className="w-4 h-4 mr-2" /> Back
        </Button>

        <Card data-testid="job-detail-card" className="p-8 bg-white rounded-2xl border border-slate-100 shadow-sm">
          {/* Header */}
          <div className="mb-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h1 data-testid="job-title" className="text-4xl font-semibold mb-2" style={{ fontFamily: 'Outfit' }}>{job.title}</h1>
                <p data-testid="job-company" className="text-xl text-slate-600">{job.company}</p>
              </div>
              {job.match_score && (
                <div data-testid="job-match-score" className="px-4 py-2 rounded-full bg-emerald-50 text-emerald-700 text-lg font-medium">
                  {Math.round(job.match_score)}% Match
                </div>
              )}
            </div>

            <div className="flex flex-wrap gap-4 text-slate-600">
              <div data-testid="job-location" className="flex items-center gap-2">
                <MapPin className="w-4 h-4" />
                <span>{job.location}</span>
              </div>
              <div data-testid="job-type" className="flex items-center gap-2">
                <Clock className="w-4 h-4" />
                <span>{job.job_type}</span>
              </div>
              {job.salary_range && (
                <div data-testid="job-salary" className="flex items-center gap-2">
                  <DollarSign className="w-4 h-4" />
                  <span>{job.salary_range}</span>
                </div>
              )}
            </div>
          </div>

          {/* Match Reasons */}
          {job.match_reasons && job.match_reasons.length > 0 && (
            <div data-testid="match-reasons-section" className="mb-6 p-6 bg-emerald-50 rounded-xl">
              <h3 className="text-lg font-semibold mb-3" style={{ fontFamily: 'Outfit' }}>Why This is a Good Match</h3>
              <ul className="space-y-2">
                {job.match_reasons.map((reason, idx) => (
                  <li key={idx} data-testid={`match-reason-${idx}`} className="flex items-start gap-2">
                    <CheckCircle className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" />
                    <span className="text-slate-700">{reason}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Description */}
          <div data-testid="job-description-section" className="mb-6">
            <h3 className="text-2xl font-semibold mb-3" style={{ fontFamily: 'Outfit' }}>Job Description</h3>
            <p className="text-lg leading-relaxed text-slate-700 whitespace-pre-line">{job.description}</p>
          </div>

          {/* Requirements */}
          <div data-testid="job-requirements-section" className="mb-6">
            <h3 className="text-2xl font-semibold mb-3" style={{ fontFamily: 'Outfit' }}>Requirements</h3>
            <ul className="space-y-2">
              {job.requirements.map((req, idx) => (
                <li key={idx} data-testid={`requirement-${idx}`} className="flex items-start gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-indigo-600 flex-shrink-0 mt-2" />
                  <span className="text-slate-700">{req}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Apply Button */}
          {user.role === 'job_seeker' && (
            <div data-testid="apply-section" className="pt-6 border-t border-slate-100">
              {hasApplied ? (
                <div data-testid="already-applied-message" className="flex items-center gap-2 text-emerald-600">
                  <CheckCircle className="w-5 h-5" />
                  <span className="font-medium">You have already applied to this job</span>
                </div>
              ) : (
                <Button
                  data-testid="apply-btn"
                  onClick={handleApply}
                  disabled={applying}
                  size="lg"
                  className="w-full rounded-full h-12 bg-indigo-600 hover:bg-indigo-700 shadow-lg shadow-indigo-500/20 font-medium"
                >
                  {applying ? (
                    <><Loader2 className="w-5 h-5 mr-2 animate-spin" /> Submitting Application...</>
                  ) : (
                    'Apply Now'
                  )}
                </Button>
              )}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
};

export default JobDetail;
