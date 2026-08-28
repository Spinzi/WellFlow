export default function Card({ icon, title, headerRight, children }) {
  return (
    <section className="card">
      <div className="card__header">
        <div className="card__title-group">
          {icon && <div className="card__icon">{icon}</div>}
          <h2 className="card__title">{title}</h2>
        </div>
        {headerRight}
      </div>
      <div className="card__body">{children}</div>
    </section>
  );
}
