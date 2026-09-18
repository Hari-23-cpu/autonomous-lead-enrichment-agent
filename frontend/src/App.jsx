import { useEffect, useState } from "react";
import "./App.css";

function App() {
  const [companies, setCompanies] = useState([]);
  const [selected, setSelected] = useState(null);
  const [domain, setDomain] = useState("");

  useEffect(() => {
    fetch("/output.json")
      .then((response) => {
        if (!response.ok) {
          throw new Error("Could not load output.json");
        }
        return response.json();
      })
      .then((data) => {
        setCompanies(data);
        if (data.length > 0) {
          setSelected(data[0]);
        }
      })
      .catch((error) => {
        console.error(error);
      });
  }, []);

  const enrichLead = async () => {
  const search = domain.trim();

  if (!search) {
    alert("Please enter a company domain.");
    return;
  }

  try {
    const response = await fetch("http://127.0.0.1:8000/enrich", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        domain: search,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Enrichment failed");
    }

    setSelected(data);

    setCompanies((previous) => {
    const exists = previous.some(
        (company) => company.domain === data.domain
      );

      if (exists) {
        return previous.map((company) =>
          company.domain === data.domain ? data : company
        );
      }

      return [data, ...previous];
    });

  } catch (error) {
    console.error(error);
    alert(`Enrichment failed: ${error.message}`);
  }
};

  return (
    <div className="app">
      <header className="navbar">
        <div className="brand">
          <div className="brand-icon">AI</div>
          <div>
            <h2>Lead Enrichment</h2>
            <span>Autonomous Intelligence Agent</span>
          </div>
        </div>

        <div className="agent-status">
          <span className="status-dot"></span>
          Agent Ready
        </div>
      </header>

      <main>
        <section className="hero">
          <div>
            <p className="eyebrow">AI-POWERED PROSPECTING</p>

            <h1>
              Turn company websites into
              <span> structured lead intelligence.</span>
            </h1>

            <p className="hero-text">
              Automatically crawl public company websites, extract useful
              business information, and transform it into structured lead data.
            </p>
          </div>

          <div className="search-box">
            <input
              type="text"
              placeholder="Enter company domain..."
              value={domain}
              onChange={(e) => setDomain(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") enrichLead();
              }}
            />

            <button onClick={enrichLead}>Enrich Lead</button>
          </div>
        </section>

        {selected && (
          <section className="content">
            <div className="section-heading">
              <div>
                <p className="eyebrow">ENRICHED COMPANY</p>
                <h2>{selected.domain}</h2>
              </div>

              <div className="confidence">
                <span>Confidence</span>
                <strong>
                  {Math.round(selected.confidence_score * 100)}%
                </strong>
              </div>
            </div>

            <div className="grid">
              <div className="card overview-card">
                <p className="card-label">COMPANY OVERVIEW</p>
                <h3>About the company</h3>
                <p>{selected.company_overview}</p>
              </div>

              <div className="card">
                <p className="card-label">TARGET AUDIENCE</p>
                <h3>Ideal customer profile</h3>

                <div className="tags">
                  {selected.target_audience
                    .split(",")
                    .map((audience, index) => (
                      <span className="tag" key={index}>
                        {audience.trim()}
                      </span>
                    ))}
                </div>
              </div>

              <div className="card">
                <p className="card-label">CONTACT POINTS</p>
                <h3>Public emails</h3>

                {selected.contact_points?.length > 0 ? (
                  selected.contact_points.map((contact, index) => (
                    <div className="contact" key={index}>
                      <span>✉</span>
                      <div>
                        <strong>{contact.email}</strong>
                        <small>{contact.source_url}</small>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="muted">No public email discovered.</p>
                )}
              </div>

              <div className="card">
                <p className="card-label">LEADERSHIP & TEAM</p>
                <h3>Key people</h3>

                {selected.leadership_team?.length > 0 ? (
                  selected.leadership_team.map((person, index) => (
                    <div className="person" key={index}>
                      <div className="avatar">
                        {person.name.charAt(0)}
                      </div>

                      <div>
                        <strong>{person.name}</strong>
                        <small>{person.role || "Role not specified"}</small>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="muted">
                    No verified leadership information discovered.
                  </p>
                )}
              </div>
            </div>
          </section>
        )}

        <section className="processed">
          <div className="section-heading">
            <div>
              <p className="eyebrow">AGENT RESULTS</p>
              <h2>Processed Companies</h2>
            </div>

            <span className="result-count">
              {companies.length} companies
            </span>
          </div>

          <div className="table-card">
            <table>
              <thead>
                <tr>
                  <th>DOMAIN</th>
                  <th>TARGET AUDIENCE</th>
                  <th>LEADERSHIP</th>
                  <th>CONFIDENCE</th>
                  <th></th>
                </tr>
              </thead>

              <tbody>
                {companies.map((company) => (
                  <tr key={company.domain}>
                    <td>
                      <strong>{company.domain}</strong>
                    </td>

                    <td>{company.target_audience}</td>

                    <td>
                      {company.leadership_team?.length || 0} verified
                    </td>

                    <td>
                      <span className="confidence-pill">
                        {Math.round(company.confidence_score * 100)}%
                      </span>
                    </td>

                    <td>
                      <button
                        className="view-button"
                        onClick={() => setSelected(company)}
                      >
                        View
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </main>

      <footer>
        <span>Lead Enrichment Agent</span>
        <span>Playwright • Ollama • Pydantic</span>
      </footer>
    </div>
  );
}

export default App;