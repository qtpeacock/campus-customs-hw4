import { Link } from 'react-router-dom'

export default function AboutPage() {
  return (
    <>
      <section className="page-banner">
        <div className="container">
          <p className="eyebrow">About us</p>
          <h1>A family shop across from campus.</h1>
          <p className="hero-copy">
            We're Campus Customs, the store at 57 Broadway in New Haven, right across the street from
            Yale. We've been selling Yale gear on Broadway since the 1970s, and we're still family-run.
          </p>
        </div>
      </section>

      <section className="section container about-grid">
        <div>
          <h2>What we make</h2>
          <p>
            Officially licensed Yale apparel: hoodies, crewnecks, quarter-zips, fleeces, and tees. Some
            of it is the classic big-YALE stuff everyone knows. A lot of it is more specific, like your
            residential college, your sport, your grad school, or The Game.
          </p>
          <p>
            We also do screen printing, embroidery, and custom merch for teams, clubs, and events, which
            is a big part of how we got here.
          </p>

          <h2>Who it's for</h2>
          <p>
            Pretty much anyone with a Yale connection. Students who need a new hoodie before the next
            game. Alums who want something that isn't from twenty years ago. Parents, grandparents,
            aunts, and uncles who want everyone to know where the family goes to school.
          </p>
        </div>

        <aside className="info-card">
          <h2>Good to know</h2>
          <ul className="detail-list">
            <li>Orders take about 5–8 business days to make before they ship, and a bit longer in busy seasons.</li>
            <li>We ship with UPS in the US, and we ship internationally too (customs fees and duties are on the buyer).</li>
            <li>You'll get an email with tracking as soon as your order ships.</li>
            <li>Returns are accepted within 30 days of shipping if the item is unworn with the original tags.</li>
            <li>Custom and final-sale items can't be returned or exchanged.</li>
            <li>If we got your order wrong or it arrived damaged, we cover the return shipping.</li>
            <li>Refunds are processed 2–10 business days after we get your return.</li>
          </ul>

          <h2>Say hi</h2>
          <p>
            57 Broadway, New Haven, CT 06511
            <br />
            <a href="mailto:orderdept@campuscustoms.com">orderdept@campuscustoms.com</a>
            <br />
            <a href="tel:+14753014205">(475) 301-4205</a>
          </p>
        </aside>
      </section>

      <section className="section section-alt">
        <div className="container chat-callout">
          <h2>Ready to look around?</h2>
          <p className="muted">Everything we carry is on one page.</p>
          <Link to="/products" className="btn btn-primary">
            Shop all products
          </Link>
        </div>
      </section>
    </>
  )
}
