// Create decomposition (§2.3): a new decomposition, saved into one of the Library's namespaces.

import { getNamespaces } from "../api";
import { DecompositionEditor } from "../components/editor";
import { Banner } from "../components/fields";
import { useLoaded } from "../load";
import type { TabProps } from "./props";

export function CreateTab(props: TabProps) {
  const namespaces = useLoaded(getNamespaces, [props.rev], props.onBackendLost);
  if (!namespaces.data) {
    return namespaces.error ? (
      <Banner kind="error">{namespaces.error.message}</Banner>
    ) : null;
  }
  return (
    <section class="create">
      <DecompositionEditor
        record={null}
        namespaces={namespaces.data}
        params={props.params}
        health={props.health}
        draftKey="create"
        onSaved={() => namespaces.reload()}
        navigateTab={props.navigateTab}
        onBackendLost={props.onBackendLost}
      />
    </section>
  );
}
